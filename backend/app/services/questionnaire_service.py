"""
Questionnaire Service for Dynamic Genetic/Epigenetic Risk Assessment

This service manages adaptive questionnaires, session handling, and risk calculations
for predicting genetic mutations and epigenetic factors.
"""

import uuid
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import redis
import logging

from app.core.config import settings
from app.services.risk_calculator import GeneticRiskCalculator
from app.services.question_bank import QuestionBank
from app.db.models import Patient

logger = logging.getLogger(__name__)

@dataclass
class QuestionnaireSession:
    session_id: str
    questionnaire_type: str
    patient_id: Optional[int]
    created_by: int
    created_at: datetime
    responses: List[Dict[str, Any]]
    current_question_index: int
    is_complete: bool
    is_paused: bool
    risk_scores: Dict[str, float]
    question_path: List[str]
    estimated_questions: int

class QuestionnaireService:
    """
    Service for managing dynamic questionnaires and risk assessment.
    """
    
    def __init__(self):
        """Initialize the questionnaire service."""
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
        self.question_bank = QuestionBank()
        self.risk_calculator = GeneticRiskCalculator()
        self.session_timeout = timedelta(hours=24)  # Sessions expire after 24 hours
        
    def create_session(
        self, 
        questionnaire_type: str, 
        patient_id: Optional[int] = None,
        created_by: int = None
    ) -> Dict[str, Any]:
        """
        Create a new questionnaire session.
        
        Args:
            questionnaire_type: Type of questionnaire (genetic_screening, epigenetic_assessment, etc.)
            patient_id: Optional patient ID
            created_by: User ID who created the session
            
        Returns:
            Dictionary containing session information
        """
        session_id = str(uuid.uuid4())
        
        # Get initial question set and estimate total questions
        initial_questions = self.question_bank.get_initial_questions(questionnaire_type)
        estimated_questions = self.question_bank.estimate_total_questions(questionnaire_type)
        
        session = QuestionnaireSession(
            session_id=session_id,
            questionnaire_type=questionnaire_type,
            patient_id=patient_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            responses=[],
            current_question_index=0,
            is_complete=False,
            is_paused=False,
            risk_scores={},
            question_path=[],
            estimated_questions=estimated_questions
        )
        
        # Store session in Redis
        self._save_session(session)
        
        logger.info(f"Created questionnaire session {session_id} of type {questionnaire_type}")
        
        return {
            "session_id": session_id,
            "questionnaire_type": questionnaire_type,
            "estimated_questions": estimated_questions,
            "created_at": session.created_at
        }
    
    def get_next_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next question in the adaptive questionnaire.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Next question dictionary or None if complete
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.is_complete:
            return None
            
        # Determine next question based on current responses and risk calculations
        next_question_id = self._determine_next_question(session)
        
        if not next_question_id:
            # No more questions, mark session as complete
            session.is_complete = True
            self._save_session(session)
            return None
        
        # Get question definition
        question = self.question_bank.get_question(next_question_id)
        if not question:
            logger.error(f"Question {next_question_id} not found in question bank")
            return None
        
        # Add session context
        question_with_context = {
            **question,
            "session_id": session_id,
            "question_number": len(session.responses) + 1,
            "total_estimated": session.estimated_questions,
            "progress_percentage": self._calculate_progress_percentage(session)
        }
        
        return question_with_context
    
    def record_response(self, session_id: str, response: Dict[str, Any]) -> bool:
        """
        Record a patient's response to a question.
        
        Args:
            session_id: Unique session identifier
            response: Response data
            
        Returns:
            True if response was recorded successfully
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.is_complete:
            raise ValueError("Cannot add responses to completed session")
        
        # Validate response
        question_id = response.get("question_id")
        if not question_id:
            raise ValueError("Response must include question_id")
        
        question = self.question_bank.get_question(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        # Validate response format
        if not self._validate_response_format(question, response):
            raise ValueError("Invalid response format for question type")
        
        # Add timestamp if not provided
        if "timestamp" not in response:
            response["timestamp"] = datetime.utcnow().isoformat()
        
        # Record response
        session.responses.append(response)
        session.question_path.append(question_id)
        
        # Update risk calculations immediately
        self._update_session_risk_scores(session)
        
        # Save updated session
        self._save_session(session)
        
        logger.info(f"Recorded response for question {question_id} in session {session_id}")
        return True
    
    def update_risk_calculations(self, session_id: str) -> Dict[str, float]:
        """
        Update risk calculations based on current responses.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Updated risk scores
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        self._update_session_risk_scores(session)
        self._save_session(session)
        
        return session.risk_scores
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session progress information.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Progress information dictionary
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        questions_answered = len(session.responses)
        progress_percentage = self._calculate_progress_percentage(session)
        estimated_remaining = max(0, session.estimated_questions - questions_answered)
        
        return {
            "session_id": session_id,
            "questions_answered": questions_answered,
            "total_estimated": session.estimated_questions,
            "progress_percentage": progress_percentage,
            "estimated_remaining": estimated_remaining,
            "is_complete": session.is_complete,
            "is_paused": session.is_paused
        }
    
    def get_interim_risk_scores(self, session_id: str) -> Dict[str, Any]:
        """
        Get current interim risk scores during questionnaire.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Interim risk scores and confidence levels
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Calculate confidence based on number of responses
        questions_answered = len(session.responses)
        confidence_factor = min(1.0, questions_answered / 10)  # Full confidence after 10 questions
        
        interim_risks = {}
        for risk_type, score in session.risk_scores.items():
            interim_risks[risk_type] = {
                "risk_score": score,
                "confidence": confidence_factor,
                "questions_contributing": self._count_contributing_questions(session, risk_type),
                "reliability": "low" if confidence_factor < 0.3 else "moderate" if confidence_factor < 0.7 else "high"
            }
        
        return interim_risks
    
    def calculate_final_results(self, session_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive final results for completed questionnaire.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Complete results including genetic predictions and recommendations
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.is_complete:
            # Mark as complete if we have enough responses
            if len(session.responses) >= 5:  # Minimum threshold
                session.is_complete = True
                self._save_session(session)
        
        # Calculate comprehensive risk assessment
        genetic_predictions = self.risk_calculator.calculate_genetic_risks(session.responses)
        epigenetic_factors = self.risk_calculator.calculate_epigenetic_risks(session.responses)
        
        # Calculate overall risk score
        overall_risk = self._calculate_overall_risk_score(genetic_predictions, epigenetic_factors)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            genetic_predictions, 
            epigenetic_factors, 
            overall_risk
        )
        
        # Determine clinical urgency
        clinical_urgency = self._determine_clinical_urgency(overall_risk, genetic_predictions)
        
        results = {
            "session_id": session_id,
            "completion_date": datetime.utcnow(),
            "total_questions_answered": len(session.responses),
            "genetic_predictions": genetic_predictions,
            "epigenetic_factors": epigenetic_factors,
            "overall_risk_score": overall_risk,
            "next_steps": recommendations,
            "clinical_urgency": clinical_urgency,
            "questionnaire_type": session.questionnaire_type
        }
        
        # Cache results for future retrieval
        self._cache_results(session_id, results)
        
        return results
    
    def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached results for a completed session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Cached results or None if not found
        """
        try:
            results_key = f"questionnaire_results:{session_id}"
            cached_results = self.redis_client.get(results_key)
            
            if cached_results:
                return json.loads(cached_results)
            
            # Try to calculate results if session exists
            session = self._load_session(session_id)
            if session and session.is_complete:
                return self.calculate_final_results(session_id)
                
        except Exception as e:
            logger.error(f"Error retrieving results for session {session_id}: {e}")
        
        return None
    
    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """
        Pause a questionnaire session for later resumption.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Pause information including resume token
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.is_complete:
            raise ValueError("Cannot pause completed session")
        
        session.is_paused = True
        resume_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + self.session_timeout
        
        # Store resume token
        resume_key = f"questionnaire_resume:{session_id}"
        self.redis_client.setex(
            resume_key, 
            int(self.session_timeout.total_seconds()), 
            resume_token
        )
        
        self._save_session(session)
        
        return {
            "resume_token": resume_token,
            "expires_at": expires_at
        }
    
    def resume_session(self, session_id: str, resume_token: str) -> Dict[str, Any]:
        """
        Resume a paused questionnaire session.
        
        Args:
            session_id: Unique session identifier
            resume_token: Token provided when session was paused
            
        Returns:
            Resume confirmation
        """
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Validate resume token
        resume_key = f"questionnaire_resume:{session_id}"
        stored_token = self.redis_client.get(resume_key)
        
        if not stored_token or stored_token != resume_token:
            raise ValueError("Invalid or expired resume token")
        
        session.is_paused = False
        self._save_session(session)
        
        # Clean up resume token
        self.redis_client.delete(resume_key)
        
        return {"resumed": True}
    
    def get_question_bank(self, questionnaire_type: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get questions from the question bank.
        
        Args:
            questionnaire_type: Type of questionnaire
            category: Optional category filter
            
        Returns:
            List of questions
        """
        return self.question_bank.get_questions_by_type(questionnaire_type, category)
    
    def validate_question_bank(self) -> Dict[str, Any]:
        """
        Validate the integrity of the question bank.
        
        Returns:
            Validation results
        """
        return self.question_bank.validate()
    
    def get_performance_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        questionnaire_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics on questionnaire performance.
        
        Args:
            start_date: Start date for analytics period
            end_date: End date for analytics period
            questionnaire_type: Filter by questionnaire type
            
        Returns:
            Performance analytics
        """
        # This would typically query a database of completed sessions
        # For now, return mock analytics
        return {
            "total_sessions": 150,
            "completed_sessions": 142,
            "completion_rate": 0.947,
            "average_questions_per_session": 12.3,
            "average_completion_time_minutes": 8.5,
            "top_genetic_risks_identified": [
                {"gene": "BRCA1", "frequency": 23},
                {"gene": "BRCA2", "frequency": 18},
                {"gene": "TP53", "frequency": 15}
            ],
            "questionnaire_accuracy": 0.892,
            "patient_satisfaction": 4.2
        }
    
    def recommend_questionnaires(self, patient: Patient) -> List[Dict[str, Any]]:
        """
        Recommend appropriate questionnaires for a patient.
        
        Args:
            patient: Patient object
            
        Returns:
            List of recommended questionnaires
        """
        recommendations = []
        
        # Basic genetic screening for all patients
        recommendations.append({
            "questionnaire_type": "genetic_screening",
            "priority": "high" if patient.age and patient.age >= 40 else "moderate",
            "reason": "Standard genetic risk assessment",
            "estimated_duration": "5-8 minutes"
        })
        
        # Cancer-specific questionnaires
        if patient.cancer_type:
            recommendations.append({
                "questionnaire_type": "epigenetic_assessment",
                "priority": "high",
                "reason": f"Epigenetic factors for {patient.cancer_type}",
                "estimated_duration": "6-10 minutes"
            })
        
        # Family history focused
        if patient.primary_diagnosis and "family history" in patient.primary_diagnosis.lower():
            recommendations.append({
                "questionnaire_type": "comprehensive_assessment",
                "priority": "high",
                "reason": "Comprehensive assessment for family history",
                "estimated_duration": "12-15 minutes"
            })
        
        return recommendations
    
    # Private helper methods
    
    def _save_session(self, session: QuestionnaireSession) -> None:
        """Save session to Redis."""
        session_key = f"questionnaire_session:{session.session_id}"
        session_data = {
            "session_id": session.session_id,
            "questionnaire_type": session.questionnaire_type,
            "patient_id": session.patient_id,
            "created_by": session.created_by,
            "created_at": session.created_at.isoformat(),
            "responses": session.responses,
            "current_question_index": session.current_question_index,
            "is_complete": session.is_complete,
            "is_paused": session.is_paused,
            "risk_scores": session.risk_scores,
            "question_path": session.question_path,
            "estimated_questions": session.estimated_questions
        }
        
        self.redis_client.setex(
            session_key,
            int(self.session_timeout.total_seconds()),
            json.dumps(session_data, default=str)
        )
    
    def _load_session(self, session_id: str) -> Optional[QuestionnaireSession]:
        """Load session from Redis."""
        session_key = f"questionnaire_session:{session_id}"
        session_data = self.redis_client.get(session_key)
        
        if not session_data:
            return None
        
        try:
            data = json.loads(session_data)
            return QuestionnaireSession(
                session_id=data["session_id"],
                questionnaire_type=data["questionnaire_type"],
                patient_id=data.get("patient_id"),
                created_by=data["created_by"],
                created_at=datetime.fromisoformat(data["created_at"]),
                responses=data.get("responses", []),
                current_question_index=data.get("current_question_index", 0),
                is_complete=data.get("is_complete", False),
                is_paused=data.get("is_paused", False),
                risk_scores=data.get("risk_scores", {}),
                question_path=data.get("question_path", []),
                estimated_questions=data.get("estimated_questions", 10)
            )
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def _determine_next_question(self, session: QuestionnaireSession) -> Optional[str]:
        """Determine the next question based on current responses."""
        return self.question_bank.get_next_question(
            session.questionnaire_type,
            session.responses,
            session.question_path
        )
    
    def _validate_response_format(self, question: Dict[str, Any], response: Dict[str, Any]) -> bool:
        """Validate that response format matches question type."""
        question_type = question.get("question_type")
        response_value = response.get("response")
        
        if question_type == "boolean":
            return isinstance(response_value, bool)
        elif question_type == "numeric":
            return isinstance(response_value, (int, float))
        elif question_type in ["multiple_choice", "text"]:
            return isinstance(response_value, str)
        elif question_type == "multi_select":
            return isinstance(response_value, list)
        
        return True  # Default to valid
    
    def _update_session_risk_scores(self, session: QuestionnaireSession) -> None:
        """Update risk scores based on current responses."""
        session.risk_scores = self.risk_calculator.calculate_interim_risks(
            session.responses,
            session.questionnaire_type
        )
    
    def _calculate_progress_percentage(self, session: QuestionnaireSession) -> float:
        """Calculate progress percentage for the session."""
        if session.estimated_questions <= 0:
            return 0.0
        
        questions_answered = len(session.responses)
        return min(100.0, (questions_answered / session.estimated_questions) * 100)
    
    def _count_contributing_questions(self, session: QuestionnaireSession, risk_type: str) -> int:
        """Count questions that contribute to a specific risk type."""
        count = 0
        for response in session.responses:
            question = self.question_bank.get_question(response.get("question_id"))
            if question and self._question_contributes_to_risk(question, risk_type):
                count += 1
        return count
    
    def _question_contributes_to_risk(self, question: Dict[str, Any], risk_type: str) -> bool:
        """Check if a question contributes to a specific risk type."""
        genetic_assoc = question.get("genetic_associations", {})
        epigenetic_assoc = question.get("epigenetic_associations", {})
        
        return risk_type in genetic_assoc or risk_type in epigenetic_assoc
    
    def _calculate_overall_risk_score(
        self, 
        genetic_predictions: List[Dict[str, Any]], 
        epigenetic_factors: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall risk score from genetic and epigenetic factors."""
        genetic_score = sum(pred.get("mutation_probability", 0) for pred in genetic_predictions) / max(1, len(genetic_predictions))
        epigenetic_score = sum(factor.get("probability_score", 0) for factor in epigenetic_factors) / max(1, len(epigenetic_factors))
        
        # Weighted combination (genetic risks weighted higher)
        return (genetic_score * 0.7 + epigenetic_score * 0.3)
    
    def _generate_recommendations(
        self, 
        genetic_predictions: List[Dict[str, Any]], 
        epigenetic_factors: List[Dict[str, Any]], 
        overall_risk: float
    ) -> List[str]:
        """Generate clinical recommendations based on risk assessment."""
        recommendations = []
        
        # High-risk genetic findings
        high_risk_genes = [pred for pred in genetic_predictions 
                          if pred.get("mutation_probability", 0) > 0.3]
        
        if high_risk_genes:
            recommendations.append("Consider genetic counseling and confirmatory testing")
            recommendations.append("Discuss family screening and cascade testing")
        
        # Epigenetic recommendations
        modifiable_factors = [factor for factor in epigenetic_factors 
                             if factor.get("modifiable", False)]
        
        if modifiable_factors:
            recommendations.append("Lifestyle modifications may reduce epigenetic risk factors")
        
        # Overall risk-based recommendations
        if overall_risk > 0.7:
            recommendations.append("Consider enhanced screening protocols")
        elif overall_risk > 0.4:
            recommendations.append("Standard screening with consideration for earlier/more frequent monitoring")
        
        return recommendations
    
    def _determine_clinical_urgency(
        self, 
        overall_risk: float, 
        genetic_predictions: List[Dict[str, Any]]
    ) -> str:
        """Determine clinical urgency level."""
        # Critical findings
        critical_genes = [pred for pred in genetic_predictions 
                         if pred.get("mutation_probability", 0) > 0.8]
        
        if critical_genes:
            return "critical"
        elif overall_risk > 0.7:
            return "urgent"
        elif overall_risk > 0.4:
            return "elevated"
        else:
            return "routine"
    
    def _cache_results(self, session_id: str, results: Dict[str, Any]) -> None:
        """Cache final results for retrieval."""
        results_key = f"questionnaire_results:{session_id}"
        self.redis_client.setex(
            results_key,
            int((self.session_timeout * 7).total_seconds()),  # Keep results for 7x session timeout
            json.dumps(results, default=str)
        )
