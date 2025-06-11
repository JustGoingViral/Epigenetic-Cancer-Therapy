"""
Comprehensive test suite for the QuestionnaireService

Tests cover session management, questionnaire flow, Redis integration,
and business logic validation.
"""

import pytest
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import the classes under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.questionnaire_service import QuestionnaireService
from services.risk_calculator import GeneticRiskCalculator
from services.question_bank import QuestionBank


class TestQuestionnaireService:
    """Test cases for QuestionnaireService class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing."""
        return Mock()
    
    @pytest.fixture
    def mock_risk_calculator(self):
        """Mock risk calculator for testing."""
        calculator = Mock(spec=GeneticRiskCalculator)
        calculator.calculate_genetic_risks.return_value = [
            {
                "gene_symbol": "BRCA1",
                "mutation_probability": 0.15,
                "confidence_interval": [0.08, 0.24],
                "evidence_strength": "moderate",
                "clinical_significance": "Test significance",
                "recommended_testing": ["Test recommendation"]
            }
        ]
        calculator.calculate_epigenetic_risks.return_value = [
            {
                "factor_name": "DNA Methylation Patterns",
                "risk_level": "moderate",
                "probability_score": 0.45,
                "modifiable": True,
                "recommendations": ["Test recommendation"]
            }
        ]
        calculator.calculate_interim_risks.return_value = {
            "highest_genetic_risk": 0.15,
            "overall_risk": 0.12
        }
        return calculator
    
    @pytest.fixture
    def mock_question_bank(self):
        """Mock question bank for testing."""
        bank = Mock(spec=QuestionBank)
        bank.get_initial_questions.return_value = ["demo_age", "demo_gender"]
        bank.estimate_total_questions.return_value = 15
        bank.get_question.return_value = {
            "question_id": "demo_age",
            "question_text": "What is your age?",
            "question_type": "numeric",
            "category": "demographics",
            "priority_weight": 10.0
        }
        bank.get_next_question.return_value = "family_cancer_history"
        return bank
    
    @pytest.fixture
    def service(self, mock_redis, mock_risk_calculator, mock_question_bank):
        """Create service instance with mocked dependencies."""
        with patch('services.questionnaire_service.redis.Redis', return_value=mock_redis), \
             patch('services.questionnaire_service.GeneticRiskCalculator', return_value=mock_risk_calculator), \
             patch('services.questionnaire_service.QuestionBank', return_value=mock_question_bank):
            return QuestionnaireService()

    def test_service_initialization(self, service):
        """Test that service initializes correctly."""
        assert service is not None
        assert hasattr(service, 'redis_client')
        assert hasattr(service, 'risk_calculator')
        assert hasattr(service, 'question_bank')

    def test_start_session(self, service, mock_redis, mock_question_bank):
        """Test starting a new questionnaire session."""
        # Setup mock Redis responses
        mock_redis.setex.return_value = True
        mock_question_bank.get_initial_questions.return_value = ["demo_age", "demo_gender"]
        mock_question_bank.estimate_total_questions.return_value = 15
        
        result = service.start_session("genetic_screening")
        
        assert "session_id" in result
        assert "questionnaire_type" in result
        assert "total_estimated_questions" in result
        assert "initial_questions" in result
        assert "created_at" in result
        
        assert result["questionnaire_type"] == "genetic_screening"
        assert result["total_estimated_questions"] == 15
        assert "demo_age" in result["initial_questions"]
        
        # Verify Redis was called to store session
        mock_redis.setex.assert_called()

    def test_get_next_question(self, service, mock_redis, mock_question_bank):
        """Test getting the next question in a session."""
        session_id = "test-session-123"
        
        # Mock session data in Redis
        session_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [
                {"question_id": "demo_age", "response": 45}
            ],
            "question_path": ["demo_age"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex.return_value = True
        mock_question_bank.get_question.return_value = {
            "question_id": "demo_gender",
            "question_text": "What is your gender?",
            "question_type": "multiple_choice",
            "options": ["Male", "Female"],
            "category": "demographics"
        }
        mock_question_bank.get_next_question.return_value = "demo_gender"
        
        result = service.get_next_question(session_id)
        
        assert "question" in result
        assert "progress" in result
        assert "complete" in result
        assert "session_id" in result
        
        assert result["question"]["question_id"] == "demo_gender"
        assert result["complete"] == False
        
        # Verify Redis get was called
        mock_redis.get.assert_called_with(f"questionnaire_session:{session_id}")

    def test_submit_response(self, service, mock_redis, mock_question_bank, mock_risk_calculator):
        """Test submitting a response to a question."""
        session_id = "test-session-123"
        
        # Mock existing session data
        session_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [],
            "question_path": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex.return_value = True
        mock_question_bank.get_next_question.return_value = "family_cancer_history"
        mock_question_bank.get_question.return_value = {
            "question_id": "family_cancer_history",
            "question_text": "Any family cancer history?",
            "question_type": "boolean"
        }
        
        response_data = {
            "question_id": "demo_age",
            "response": 45,
            "confidence": 1.0
        }
        
        result = service.submit_response(session_id, response_data)
        
        assert "next_question" in result
        assert "progress" in result
        assert "complete" in result
        assert "updated_risks" in result
        
        assert result["next_question"]["question_id"] == "family_cancer_history"
        assert result["complete"] == False
        
        # Verify response was stored
        mock_redis.setex.assert_called()

    def test_submit_response_completion(self, service, mock_redis, mock_question_bank, mock_risk_calculator):
        """Test submitting final response that completes questionnaire."""
        session_id = "test-session-123"
        
        # Mock session data with many responses
        session_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [
                {"question_id": "demo_age", "response": 45},
                {"question_id": "demo_gender", "response": "Female"},
                {"question_id": "family_cancer_history", "response": True}
            ],
            "question_path": ["demo_age", "demo_gender", "family_cancer_history"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex.return_value = True
        mock_question_bank.get_next_question.return_value = None  # No more questions
        
        response_data = {
            "question_id": "family_cancer_types",
            "response": ["Breast cancer"],
            "confidence": 1.0
        }
        
        result = service.submit_response(session_id, response_data)
        
        assert result["complete"] == True
        assert "final_results" in result
        assert "genetic_risks" in result["final_results"]
        assert "epigenetic_risks" in result["final_results"]
        
        # Verify risk calculations were called
        mock_risk_calculator.calculate_genetic_risks.assert_called()
        mock_risk_calculator.calculate_epigenetic_risks.assert_called()

    def test_get_session_results(self, service, mock_redis, mock_risk_calculator):
        """Test retrieving session results."""
        session_id = "test-session-123"
        
        # Mock completed session data
        session_data = {
            "questionnaire_type": "comprehensive_assessment",
            "responses": [
                {"question_id": "demo_age", "response": 45},
                {"question_id": "family_cancer_history", "response": True}
            ],
            "question_path": ["demo_age", "family_cancer_history"],
            "completed": True,
            "completed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        
        result = service.get_session_results(session_id)
        
        assert "session_id" in result
        assert "questionnaire_type" in result
        assert "completion_status" in result
        assert "genetic_risks" in result
        assert "epigenetic_risks" in result
        assert "clinical_recommendations" in result
        
        assert result["completion_status"] == "completed"
        
        # Verify calculations were performed
        mock_risk_calculator.calculate_genetic_risks.assert_called()
        mock_risk_calculator.calculate_epigenetic_risks.assert_called()

    def test_pause_session(self, service, mock_redis):
        """Test pausing a session."""
        session_id = "test-session-123"
        
        # Mock existing session
        session_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [{"question_id": "demo_age", "response": 45}],
            "question_path": ["demo_age"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex.return_value = True
        
        result = service.pause_session(session_id)
        
        assert "status" in result
        assert "resume_token" in result
        assert "paused_at" in result
        
        assert result["status"] == "paused"
        
        # Verify session was updated with pause info
        mock_redis.setex.assert_called()

    def test_resume_session(self, service, mock_redis):
        """Test resuming a paused session."""
        resume_token = "resume-token-123"
        
        # Mock paused session data
        session_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [{"question_id": "demo_age", "response": 45}],
            "question_path": ["demo_age"],
            "status": "paused",
            "paused_at": datetime.now().isoformat(),
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        mock_redis.setex.return_value = True
        
        result = service.resume_session(resume_token)
        
        assert "session_id" in result
        assert "questionnaire_type" in result
        assert "progress" in result
        assert "status" in result
        
        assert result["status"] == "active"
        
        # Verify session was reactivated
        mock_redis.setex.assert_called()

    def test_get_session_analytics(self, service, mock_redis):
        """Test getting session analytics."""
        session_id = "test-session-123"
        
        # Mock session with timing data
        session_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [
                {"question_id": "demo_age", "response": 45, "timestamp": datetime.now().isoformat()},
                {"question_id": "demo_gender", "response": "Female", "timestamp": datetime.now().isoformat()}
            ],
            "question_path": ["demo_age", "demo_gender"],
            "created_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(session_data)
        
        result = service.get_session_analytics(session_id)
        
        assert "session_id" in result
        assert "total_time_minutes" in result
        assert "questions_answered" in result
        assert "avg_time_per_question" in result
        assert "completion_percentage" in result
        
        assert result["questions_answered"] == 2
        assert result["completion_percentage"] > 0

    def test_validate_session_data(self, service):
        """Test session data validation."""
        # Valid session data
        valid_data = {
            "questionnaire_type": "genetic_screening",
            "responses": [],
            "question_path": [],
            "created_at": datetime.now().isoformat()
        }
        
        is_valid, errors = service._validate_session_data(valid_data)
        assert is_valid == True
        assert len(errors) == 0
        
        # Invalid session data
        invalid_data = {
            "responses": [],
            "question_path": []
            # Missing required fields
        }
        
        is_valid, errors = service._validate_session_data(invalid_data)
        assert is_valid == False
        assert len(errors) > 0

    def test_calculate_progress(self, service):
        """Test progress calculation."""
        responses = [
            {"question_id": "demo_age", "response": 45},
            {"question_id": "demo_gender", "response": "Female"}
        ]
        
        progress = service._calculate_progress(responses, 15)
        
        assert "questions_answered" in progress
        assert "total_estimated" in progress
        assert "progress_percentage" in progress
        
        assert progress["questions_answered"] == 2
        assert progress["total_estimated"] == 15
        assert progress["progress_percentage"] == pytest.approx(13.33, rel=1e-2)

    def test_generate_clinical_recommendations(self, service):
        """Test clinical recommendations generation."""
        genetic_risks = [
            {
                "gene_symbol": "BRCA1",
                "mutation_probability": 0.25,
                "evidence_strength": "high"
            }
        ]
        
        epigenetic_risks = [
            {
                "factor_name": "DNA Methylation Patterns",
                "risk_level": "high",
                "modifiable": True
            }
        ]
        
        recommendations = service._generate_clinical_recommendations(genetic_risks, epigenetic_risks)
        
        assert "genetic_testing" in recommendations
        assert "lifestyle_modifications" in recommendations
        assert "follow_up" in recommendations
        assert "urgency_level" in recommendations
        
        # High BRCA1 risk should result in urgent recommendations
        assert recommendations["urgency_level"] in ["elevated", "urgent"]

    def test_session_expiry_handling(self, service, mock_redis):
        """Test handling of expired sessions."""
        session_id = "expired-session"
        
        # Mock Redis returning None (expired session)
        mock_redis.get.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            service.get_next_question(session_id)
        
        assert "Session not found" in str(exc_info.value)

    def test_invalid_session_data_handling(self, service, mock_redis):
        """Test handling of corrupted session data."""
        session_id = "corrupted-session"
        
        # Mock Redis returning invalid JSON
        mock_redis.get.return_value = "invalid json data"
        
        with pytest.raises(ValueError) as exc_info:
            service.get_next_question(session_id)
        
        assert "Invalid session data" in str(exc_info.value)

    def test_response_validation(self, service):
        """Test response data validation."""
        # Valid response
        valid_response = {
            "question_id": "demo_age",
            "response": 45,
            "confidence": 1.0
        }
        
        is_valid, errors = service._validate_response(valid_response)
        assert is_valid == True
        assert len(errors) == 0
        
        # Invalid response - missing required fields
        invalid_response = {
            "response": 45
            # Missing question_id
        }
        
        is_valid, errors = service._validate_response(invalid_response)
        assert is_valid == False
        assert len(errors) > 0

    def test_session_security(self, service):
        """Test session security measures."""
        # Test session ID generation
        session_id1 = service._generate_session_id()
        session_id2 = service._generate_session_id()
        
        assert session_id1 != session_id2
        assert len(session_id1) >= 16  # Reasonable length
        assert isinstance(session_id1, str)
        
        # Test resume token generation
        token1 = service._generate_resume_token()
        token2 = service._generate_resume_token()
        
        assert token1 != token2
        assert len(token1) >= 32  # Should be longer than session ID

    def test_concurrent_session_handling(self, service, mock_redis):
        """Test handling of concurrent session operations."""
        session_id = "concurrent-session"
        
        # Mock Redis operations
        mock_redis.get.return_value = json.dumps({
            "questionnaire_type": "genetic_screening",
            "responses": [],
            "question_path": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        mock_redis.setex.return_value = True
        
        # Simulate concurrent responses
        response1 = {"question_id": "demo_age", "response": 45, "confidence": 1.0}
        response2 = {"question_id": "demo_gender", "response": "Female", "confidence": 1.0}
        
        # Both operations should succeed (Redis handles concurrency)
        result1 = service.submit_response(session_id, response1)
        result2 = service.submit_response(session_id, response2)
        
        assert "next_question" in result1
        assert "next_question" in result2

    def test_performance_benchmarks(self, service, mock_redis, mock_question_bank):
        """Test performance benchmarks for service operations."""
        import time
        
        # Mock Redis responses for performance testing
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = json.dumps({
            "questionnaire_type": "genetic_screening",
            "responses": [],
            "question_path": [],
            "created_at": datetime.now().isoformat()
        })
        
        # Test session creation performance
        start_time = time.time()
        for _ in range(100):
            service.start_session("genetic_screening")
        creation_time = time.time() - start_time
        
        assert creation_time < 2.0  # Should create 100 sessions in < 2 seconds
        
        # Test response submission performance
        start_time = time.time()
        for i in range(100):
            service.submit_response(f"session-{i}", {
                "question_id": "demo_age",
                "response": 25 + i,
                "confidence": 1.0
            })
        submission_time = time.time() - start_time
        
        assert submission_time < 3.0  # Should handle 100 submissions in < 3 seconds

    def test_error_recovery(self, service, mock_redis):
        """Test error recovery mechanisms."""
        session_id = "error-test-session"
        
        # Test Redis connection failure simulation
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        with pytest.raises(Exception) as exc_info:
            service.get_next_question(session_id)
        
        # Service should propagate Redis errors appropriately
        assert "Redis connection failed" in str(exc_info.value)
        
        # Reset mock for subsequent tests
        mock_redis.get.side_effect = None

    def test_data_consistency(self, service, mock_redis):
        """Test data consistency across operations."""
        session_id = "consistency-test"
        
        # Mock initial session state
        initial_session = {
            "questionnaire_type": "genetic_screening",
            "responses": [],
            "question_path": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(initial_session)
        mock_redis.setex.return_value = True
        
        # Submit multiple responses
        responses = [
            {"question_id": "demo_age", "response": 45, "confidence": 1.0},
            {"question_id": "demo_gender", "response": "Female", "confidence": 1.0},
            {"question_id": "family_cancer_history", "response": True, "confidence": 1.0}
        ]
        
        for response in responses:
            service.submit_response(session_id, response)
        
        # Verify Redis setex was called for each response
        assert mock_redis.setex.call_count >= len(responses)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
