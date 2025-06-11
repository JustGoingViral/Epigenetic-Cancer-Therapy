"""
Question Bank for Dynamic Genetic/Epigenetic Risk Assessment

This service manages the evidence-based question database with genetic associations,
adaptive logic, and clinical decision trees for personalized risk assessment.
"""

import json
import random
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Question:
    """Data class representing a single question."""
    question_id: str
    question_text: str
    question_type: str
    options: Optional[List[str]]
    validation_rules: Optional[Dict[str, Any]]
    genetic_associations: Optional[Dict[str, float]]
    epigenetic_associations: Optional[Dict[str, float]]
    category: str
    priority_weight: float
    skip_conditions: Optional[Dict[str, Any]]
    follow_up_questions: Optional[List[str]]

class QuestionBank:
    """
    Comprehensive question bank with evidence-based genetic and epigenetic associations.
    """
    
    def __init__(self):
        """Initialize the question bank with evidence-based questions."""
        self.questions = self._initialize_questions()
        self.decision_trees = self._initialize_decision_trees()
        self.question_dependencies = self._initialize_dependencies()
        
    def get_initial_questions(self, questionnaire_type: str) -> List[str]:
        """
        Get the initial set of questions for a questionnaire type.
        
        Args:
            questionnaire_type: Type of questionnaire
            
        Returns:
            List of initial question IDs
        """
        initial_questions = []
        
        if questionnaire_type == "genetic_screening":
            initial_questions = [
                "demo_age", "demo_gender", "demo_ethnicity",
                "family_cancer_history", "personal_cancer_history"
            ]
        elif questionnaire_type == "epigenetic_assessment":
            initial_questions = [
                "demo_age", "lifestyle_smoking", "lifestyle_alcohol",
                "diet_quality", "stress_level"
            ]
        elif questionnaire_type == "comprehensive_assessment":
            initial_questions = [
                "demo_age", "demo_gender", "demo_ethnicity",
                "family_cancer_history", "lifestyle_smoking"
            ]
        
        return initial_questions
    
    def estimate_total_questions(self, questionnaire_type: str) -> int:
        """
        Estimate total number of questions for a questionnaire type.
        
        Args:
            questionnaire_type: Type of questionnaire
            
        Returns:
            Estimated number of questions
        """
        estimates = {
            "genetic_screening": 15,
            "epigenetic_assessment": 12,
            "comprehensive_assessment": 25
        }
        
        return estimates.get(questionnaire_type, 10)
    
    def get_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific question by ID.
        
        Args:
            question_id: Question identifier
            
        Returns:
            Question dictionary or None if not found
        """
        return self.questions.get(question_id)
    
    def get_next_question(
        self, 
        questionnaire_type: str, 
        responses: List[Dict[str, Any]], 
        question_path: List[str]
    ) -> Optional[str]:
        """
        Determine the next question based on adaptive logic.
        
        Args:
            questionnaire_type: Type of questionnaire
            responses: Previous responses
            question_path: Previously asked questions
            
        Returns:
            Next question ID or None if complete
        """
        # Get decision tree for questionnaire type
        decision_tree = self.decision_trees.get(questionnaire_type, {})
        
        # Extract key information from responses
        response_map = {r.get("question_id"): r.get("response") for r in responses}
        
        # Find candidate questions
        candidate_questions = self._find_candidate_questions(
            questionnaire_type, response_map, question_path
        )
        
        if not candidate_questions:
            return None
        
        # Apply adaptive logic to select best next question
        next_question = self._select_next_question(
            candidate_questions, response_map, questionnaire_type
        )
        
        return next_question
    
    def get_questions_by_type(
        self, 
        questionnaire_type: str, 
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all questions for a questionnaire type.
        
        Args:
            questionnaire_type: Type of questionnaire
            category: Optional category filter
            
        Returns:
            List of questions
        """
        relevant_questions = []
        
        for question_id, question in self.questions.items():
            # Check if question is relevant for questionnaire type
            if self._is_question_relevant(question, questionnaire_type):
                if category is None or question.get("category") == category:
                    relevant_questions.append({
                        "question_id": question_id,
                        **question
                    })
        
        return relevant_questions
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate the integrity of the question bank.
        
        Returns:
            Validation results
        """
        issues = []
        stats = {}
        
        # Count questions by category
        categories = {}
        genetic_associations = 0
        epigenetic_associations = 0
        
        for question_id, question in self.questions.items():
            category = question.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            if question.get("genetic_associations"):
                genetic_associations += 1
            
            if question.get("epigenetic_associations"):
                epigenetic_associations += 1
            
            # Validate question structure
            if not question.get("question_text"):
                issues.append(f"Question {question_id} missing question_text")
            
            if not question.get("question_type"):
                issues.append(f"Question {question_id} missing question_type")
        
        stats = {
            "total_questions": len(self.questions),
            "categories": categories,
            "genetic_associations": genetic_associations,
            "epigenetic_associations": epigenetic_associations
        }
        
        recommendations = []
        if genetic_associations < 10:
            recommendations.append("Consider adding more questions with genetic associations")
        if epigenetic_associations < 8:
            recommendations.append("Consider adding more questions with epigenetic associations")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": stats,
            "recommendations": recommendations
        }
    
    # Private helper methods
    
    def _initialize_questions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the comprehensive question bank."""
        questions = {}
        
        # Demographics questions
        questions.update(self._get_demographic_questions())
        
        # Family history questions
        questions.update(self._get_family_history_questions())
        
        # Personal medical history questions
        questions.update(self._get_medical_history_questions())
        
        # Lifestyle questions
        questions.update(self._get_lifestyle_questions())
        
        # Environmental exposure questions
        questions.update(self._get_environmental_questions())
        
        # Symptom-based questions
        questions.update(self._get_symptom_questions())
        
        # Cancer-specific questions
        questions.update(self._get_cancer_specific_questions())
        
        return questions
    
    def _get_demographic_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get demographic questions."""
        return {
            "demo_age": {
                "question_text": "What is your current age?",
                "question_type": "numeric",
                "validation_rules": {"min": 0, "max": 120},
                "category": "demographics",
                "priority_weight": 10.0,
                "genetic_associations": {
                    "BRCA1": 0.2, "BRCA2": 0.2, "TP53": 0.3
                },
                "epigenetic_associations": {
                    "telomere_dysfunction": 0.4, "oxidative_stress": 0.3
                }
            },
            
            "demo_gender": {
                "question_text": "What is your biological sex assigned at birth?",
                "question_type": "multiple_choice",
                "options": ["Male", "Female", "Intersex", "Prefer not to answer"],
                "category": "demographics",
                "priority_weight": 8.0,
                "genetic_associations": {
                    "BRCA1": 0.4, "BRCA2": 0.4, "CDH1": 0.2
                }
            },
            
            "demo_ethnicity": {
                "question_text": "What is your ethnic background? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Ashkenazi Jewish", "Caucasian/White", "African American/Black",
                    "Hispanic/Latino", "Asian", "Native American", "Pacific Islander",
                    "Middle Eastern", "Other", "Prefer not to answer"
                ],
                "category": "demographics",
                "priority_weight": 7.0,
                "genetic_associations": {
                    "BRCA1": 0.6, "BRCA2": 0.6  # Higher for Ashkenazi Jewish
                }
            }
        }
    
    def _get_family_history_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get family history questions."""
        return {
            "family_cancer_history": {
                "question_text": "Has anyone in your family been diagnosed with cancer?",
                "question_type": "boolean",
                "category": "family_history",
                "priority_weight": 9.5,
                "genetic_associations": {
                    "BRCA1": 0.8, "BRCA2": 0.8, "TP53": 0.7, "MLH1": 0.6, "MSH2": 0.6
                },
                "follow_up_questions": ["family_cancer_types", "family_cancer_relatives"]
            },
            
            "family_cancer_types": {
                "question_text": "What types of cancer have been diagnosed in your family? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Breast cancer", "Ovarian cancer", "Prostate cancer", "Colorectal cancer",
                    "Pancreatic cancer", "Lung cancer", "Melanoma", "Gastric cancer",
                    "Endometrial cancer", "Brain cancer", "Leukemia/Lymphoma", "Other"
                ],
                "category": "family_history",
                "priority_weight": 9.0,
                "skip_conditions": {"family_cancer_history": False},
                "genetic_associations": {
                    "BRCA1": 0.9, "BRCA2": 0.8, "MLH1": 0.7, "MSH2": 0.7, "APC": 0.6
                }
            },
            
            "family_cancer_relatives": {
                "question_text": "Which family members have been diagnosed with cancer? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Mother", "Father", "Sister", "Brother", "Maternal grandmother",
                    "Maternal grandfather", "Paternal grandmother", "Paternal grandfather",
                    "Aunt (mother's side)", "Aunt (father's side)", "Uncle (mother's side)",
                    "Uncle (father's side)", "Cousin", "Other relative"
                ],
                "category": "family_history",
                "priority_weight": 8.5,
                "skip_conditions": {"family_cancer_history": False},
                "genetic_associations": {
                    "BRCA1": 0.7, "BRCA2": 0.7, "TP53": 0.6
                }
            },
            
            "family_early_onset": {
                "question_text": "Were any family members diagnosed with cancer before age 50?",
                "question_type": "boolean",
                "category": "family_history",
                "priority_weight": 8.0,
                "skip_conditions": {"family_cancer_history": False},
                "genetic_associations": {
                    "BRCA1": 0.8, "BRCA2": 0.7, "TP53": 0.9, "MLH1": 0.6
                }
            },
            
            "family_multiple_cancers": {
                "question_text": "Has any family member been diagnosed with more than one primary cancer?",
                "question_type": "boolean",
                "category": "family_history",
                "priority_weight": 7.5,
                "skip_conditions": {"family_cancer_history": False},
                "genetic_associations": {
                    "TP53": 0.9, "BRCA1": 0.6, "BRCA2": 0.6, "MLH1": 0.7
                }
            }
        }
    
    def _get_medical_history_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get personal medical history questions."""
        return {
            "personal_cancer_history": {
                "question_text": "Have you ever been diagnosed with cancer?",
                "question_type": "boolean",
                "category": "medical_history",
                "priority_weight": 9.0,
                "genetic_associations": {
                    "BRCA1": 0.6, "BRCA2": 0.6, "TP53": 0.8, "MLH1": 0.5
                },
                "follow_up_questions": ["personal_cancer_type", "personal_cancer_age"]
            },
            
            "personal_cancer_type": {
                "question_text": "What type(s) of cancer have you been diagnosed with? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Breast cancer", "Ovarian cancer", "Prostate cancer", "Colorectal cancer",
                    "Pancreatic cancer", "Lung cancer", "Melanoma", "Gastric cancer",
                    "Endometrial cancer", "Brain cancer", "Leukemia/Lymphoma", "Other"
                ],
                "category": "medical_history",
                "priority_weight": 8.5,
                "skip_conditions": {"personal_cancer_history": False},
                "genetic_associations": {
                    "BRCA1": 0.8, "BRCA2": 0.7, "TP53": 0.9
                }
            },
            
            "personal_cancer_age": {
                "question_text": "At what age were you first diagnosed with cancer?",
                "question_type": "numeric",
                "validation_rules": {"min": 0, "max": 100},
                "category": "medical_history",
                "priority_weight": 8.0,
                "skip_conditions": {"personal_cancer_history": False},
                "genetic_associations": {
                    "BRCA1": 0.7, "BRCA2": 0.6, "TP53": 0.8
                }
            },
            
            "previous_genetic_testing": {
                "question_text": "Have you ever had genetic testing for cancer susceptibility?",
                "question_type": "boolean",
                "category": "medical_history",
                "priority_weight": 6.0,
                "follow_up_questions": ["genetic_testing_results"]
            },
            
            "chronic_conditions": {
                "question_text": "Do you have any of the following chronic conditions? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Diabetes", "Heart disease", "High blood pressure", "Autoimmune disease",
                    "Inflammatory bowel disease", "Thyroid disorders", "None of the above"
                ],
                "category": "medical_history",
                "priority_weight": 5.0,
                "epigenetic_associations": {
                    "inflammation_markers": 0.6, "metabolic_dysfunction": 0.7, "oxidative_stress": 0.5
                }
            }
        }
    
    def _get_lifestyle_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get lifestyle-related questions."""
        return {
            "lifestyle_smoking": {
                "question_text": "Do you currently smoke or have you ever smoked tobacco products?",
                "question_type": "multiple_choice",
                "options": ["Never smoked", "Former smoker", "Current smoker"],
                "category": "lifestyle",
                "priority_weight": 8.0,
                "epigenetic_associations": {
                    "dna_methylation_dysregulation": 0.8, "oxidative_stress": 0.9,
                    "inflammation_markers": 0.7, "telomere_dysfunction": 0.6
                },
                "follow_up_questions": ["smoking_duration", "smoking_amount"]
            },
            
            "lifestyle_alcohol": {
                "question_text": "How often do you consume alcoholic beverages?",
                "question_type": "multiple_choice",
                "options": [
                    "Never", "Rarely (few times per year)", "Occasionally (1-2 times per month)",
                    "Regularly (1-2 times per week)", "Frequently (3-4 times per week)",
                    "Daily or almost daily"
                ],
                "category": "lifestyle",
                "priority_weight": 7.0,
                "epigenetic_associations": {
                    "dna_methylation_dysregulation": 0.6, "oxidative_stress": 0.7,
                    "inflammation_markers": 0.5
                },
                "genetic_associations": {
                    "BRCA1": 0.3, "BRCA2": 0.3
                }
            },
            
            "lifestyle_exercise": {
                "question_text": "How often do you engage in moderate to vigorous physical exercise?",
                "question_type": "multiple_choice",
                "options": [
                    "Never", "Rarely (less than once per week)", "1-2 times per week",
                    "3-4 times per week", "5+ times per week", "Daily"
                ],
                "category": "lifestyle",
                "priority_weight": 6.5,
                "epigenetic_associations": {
                    "telomere_dysfunction": -0.4,  # Negative = protective
                    "inflammation_markers": -0.3, "oxidative_stress": -0.2
                }
            },
            
            "lifestyle_sleep": {
                "question_text": "How would you rate your sleep quality over the past month?",
                "question_type": "multiple_choice",
                "options": ["Very poor", "Poor", "Fair", "Good", "Excellent"],
                "category": "lifestyle",
                "priority_weight": 5.5,
                "epigenetic_associations": {
                    "telomere_dysfunction": 0.4, "oxidative_stress": 0.3, "inflammation_markers": 0.3
                }
            },
            
            "stress_level": {
                "question_text": "How would you rate your overall stress level in the past 6 months?",
                "question_type": "multiple_choice",
                "options": ["Very low", "Low", "Moderate", "High", "Very high"],
                "category": "lifestyle",
                "priority_weight": 6.0,
                "epigenetic_associations": {
                    "telomere_dysfunction": 0.5, "inflammation_markers": 0.6, "oxidative_stress": 0.4
                }
            }
        }
    
    def _get_environmental_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get environmental exposure questions."""
        return {
            "environmental_exposures": {
                "question_text": "Have you been exposed to any of the following environmental factors? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Asbestos", "Radiation (medical or occupational)", "Industrial chemicals",
                    "Pesticides", "Heavy metals", "Air pollution", "Secondhand smoke",
                    "Occupational dust", "None of the above"
                ],
                "category": "environmental",
                "priority_weight": 6.5,
                "epigenetic_associations": {
                    "dna_methylation_dysregulation": 0.6, "oxidative_stress": 0.8,
                    "inflammation_markers": 0.5
                },
                "genetic_associations": {
                    "TP53": 0.4, "BRCA1": 0.2, "BRCA2": 0.2
                }
            },
            
            "occupational_history": {
                "question_text": "Have you worked in any of the following industries? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Chemical manufacturing", "Mining", "Construction", "Agriculture",
                    "Healthcare", "Nuclear industry", "Textile industry", "None of the above"
                ],
                "category": "environmental",
                "priority_weight": 5.0,
                "epigenetic_associations": {
                    "oxidative_stress": 0.4, "inflammation_markers": 0.3
                }
            }
        }
    
    def _get_symptom_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get symptom-based questions."""
        return {
            "current_symptoms": {
                "question_text": "Are you currently experiencing any of the following symptoms? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Unexplained weight loss", "Persistent fatigue", "Unusual lumps or bumps",
                    "Changes in bowel habits", "Unusual bleeding", "Persistent cough",
                    "Changes in moles or skin", "Difficulty swallowing", "None of the above"
                ],
                "category": "symptoms",
                "priority_weight": 7.5,
                "genetic_associations": {
                    "TP53": 0.4, "BRCA1": 0.3, "BRCA2": 0.3, "MLH1": 0.3, "APC": 0.3
                }
            }
        }
    
    def _get_cancer_specific_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get cancer-specific detailed questions."""
        return {
            "reproductive_history": {
                "question_text": "What is your reproductive history? (Select all that apply)",
                "question_type": "multi_select",
                "options": [
                    "Never pregnant", "1-2 pregnancies", "3+ pregnancies",
                    "First pregnancy after age 30", "Early menarche (before age 12)",
                    "Late menopause (after age 55)", "Use of hormone replacement therapy",
                    "Use of oral contraceptives", "Not applicable"
                ],
                "category": "reproductive",
                "priority_weight": 6.0,
                "genetic_associations": {
                    "BRCA1": 0.4, "BRCA2": 0.4
                },
                "epigenetic_associations": {
                    "dna_methylation_dysregulation": 0.3
                }
            },
            
            "diet_quality": {
                "question_text": "How would you describe your typical diet?",
                "question_type": "multiple_choice",
                "options": [
                    "Mostly processed/fast foods", "Some processed foods with home cooking",
                    "Balanced diet with occasional processed foods", "Mostly whole foods",
                    "Strict healthy diet (Mediterranean, plant-based, etc.)"
                ],
                "category": "diet",
                "priority_weight": 6.5,
                "epigenetic_associations": {
                    "dna_methylation_dysregulation": 0.5, "inflammation_markers": 0.6,
                    "oxidative_stress": 0.4, "metabolic_dysfunction": 0.7
                }
            }
        }
    
    def _initialize_decision_trees(self) -> Dict[str, Dict[str, Any]]:
        """Initialize decision trees for adaptive questioning."""
        return {
            "genetic_screening": {
                "primary_path": ["demo_age", "demo_gender", "family_cancer_history"],
                "branch_conditions": {
                    "family_cancer_history": {
                        True: ["family_cancer_types", "family_cancer_relatives", "family_early_onset"],
                        False: ["personal_cancer_history", "demo_ethnicity"]
                    }
                }
            },
            "epigenetic_assessment": {
                "primary_path": ["lifestyle_smoking", "lifestyle_alcohol", "stress_level"],
                "branch_conditions": {
                    "lifestyle_smoking": {
                        "Current smoker": ["smoking_duration", "smoking_amount"],
                        "Former smoker": ["smoking_duration"]
                    }
                }
            },
            "comprehensive_assessment": {
                "primary_path": ["demo_age", "family_cancer_history", "lifestyle_smoking", "diet_quality"],
                "branch_conditions": {
                    "family_cancer_history": {
                        True: ["family_cancer_types", "family_early_onset", "family_multiple_cancers"],
                        False: ["personal_cancer_history", "environmental_exposures"]
                    }
                }
            }
        }
    
    def _initialize_dependencies(self) -> Dict[str, List[str]]:
        """Initialize question dependencies."""
        return {
            "family_cancer_types": ["family_cancer_history"],
            "family_cancer_relatives": ["family_cancer_history"],
            "family_early_onset": ["family_cancer_history"],
            "personal_cancer_type": ["personal_cancer_history"],
            "personal_cancer_age": ["personal_cancer_history"],
            "genetic_testing_results": ["previous_genetic_testing"]
        }
    
    def _find_candidate_questions(
        self, 
        questionnaire_type: str, 
        response_map: Dict[str, Any], 
        question_path: List[str]
    ) -> List[str]:
        """Find candidate questions that haven't been asked yet."""
        candidates = []
        
        for question_id, question in self.questions.items():
            # Skip if already asked
            if question_id in question_path:
                continue
            
            # Check if question is relevant for questionnaire type
            if not self._is_question_relevant(question, questionnaire_type):
                continue
            
            # Check dependencies
            if not self._check_dependencies(question_id, response_map):
                continue
            
            # Check skip conditions
            if self._should_skip_question(question, response_map):
                continue
            
            candidates.append(question_id)
        
        return candidates
    
    def _select_next_question(
        self, 
        candidates: List[str], 
        response_map: Dict[str, Any], 
        questionnaire_type: str
    ) -> Optional[str]:
        """Select the best next question from candidates."""
        if not candidates:
            return None
        
        # Score candidates based on priority and relevance
        scored_candidates = []
        
        for question_id in candidates:
            question = self.questions[question_id]
            score = question.get("priority_weight", 1.0)
            
            # Boost score based on previous responses
            score += self._calculate_relevance_boost(question, response_map)
            
            scored_candidates.append((question_id, score))
        
        # Sort by score (highest first) and return top candidate
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return scored_candidates[0][0]
    
    def _is_question_relevant(self, question: Dict[str, Any], questionnaire_type: str) -> bool:
        """Check if a question is relevant for the questionnaire type."""
        # All questions are potentially relevant for comprehensive assessment
        if questionnaire_type == "comprehensive_assessment":
            return True
        
        # For genetic screening, prioritize questions with genetic associations
        if questionnaire_type == "genetic_screening":
            has_genetic = question.get("genetic_associations") is not None
            is_core_demo = question.get("category") in ["demographics", "family_history", "medical_history"]
            return has_genetic or is_core_demo
        
        # For epigenetic assessment, prioritize questions with epigenetic associations
        if questionnaire_type == "epigenetic_assessment":
            has_epigenetic = question.get("epigenetic_associations") is not None
            is_lifestyle = question.get("category") in ["lifestyle", "environmental", "diet"]
            return has_epigenetic or is_lifestyle
        
        return True
    
    def _check_dependencies(self, question_id: str, response_map: Dict[str, Any]) -> bool:
        """Check if question dependencies are satisfied."""
        dependencies = self.question_dependencies.get(question_id, [])
        
        for dep in dependencies:
            if dep not in response_map:
                return False
        
        return True
    
    def _should_skip_question(self, question: Dict[str, Any], response_map: Dict[str, Any]) -> bool:
        """Check if question should be skipped based on skip conditions."""
        skip_conditions = question.get("skip_conditions", {})
        
        for condition_q, condition_value in skip_conditions.items():
            response_value = response_map.get(condition_q)
            
            if response_value == condition_value:
                return True
        
        return False
    
    def _calculate_relevance_boost(self, question: Dict[str, Any], response_map: Dict[str, Any]) -> float:
        """Calculate relevance boost based on previous responses."""
        boost = 0.0
        
        # Boost family history questions if family cancer history is positive
        if response_map.get("family_cancer_history") is True:
            if question.get("category") == "family_history":
                boost += 2.0
        
        # Boost lifestyle questions if high-risk factors identified
        if response_map.get("lifestyle_smoking") in ["Current smoker", "Former smoker"]:
            if question.get("category") in ["lifestyle", "environmental"]:
                boost += 1.5
        
        # Boost genetic questions if personal cancer history is positive
        if response_map.get("personal_cancer_history") is True:
            if question.get("genetic_associations"):
                boost += 2.5
        
        return boost
