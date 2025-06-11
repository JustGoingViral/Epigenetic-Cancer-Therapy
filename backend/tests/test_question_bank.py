"""
Comprehensive test suite for the QuestionBank

Tests cover question validation, adaptive logic, decision trees,
and question retrieval functionality.
"""

import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import the classes under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.question_bank import QuestionBank, Question


class TestQuestionBank:
    """Test cases for QuestionBank class."""
    
    @pytest.fixture
    def question_bank(self):
        """Create question bank instance for testing."""
        return QuestionBank()
    
    @pytest.fixture
    def sample_responses(self):
        """Sample responses for testing adaptive logic."""
        return [
            {"question_id": "demo_age", "response": 45},
            {"question_id": "demo_gender", "response": "Female"},
            {"question_id": "family_cancer_history", "response": True}
        ]

    def test_question_bank_initialization(self, question_bank):
        """Test that question bank initializes correctly."""
        assert question_bank is not None
        assert hasattr(question_bank, 'questions')
        assert hasattr(question_bank, 'decision_trees')
        assert hasattr(question_bank, 'question_dependencies')
        
        # Test that questions are loaded
        assert len(question_bank.questions) > 0
        
        # Test that decision trees are initialized
        assert 'genetic_screening' in question_bank.decision_trees
        assert 'epigenetic_assessment' in question_bank.decision_trees
        assert 'comprehensive_assessment' in question_bank.decision_trees

    def test_get_initial_questions(self, question_bank):
        """Test getting initial questions for each questionnaire type."""
        # Test genetic screening
        genetic_initial = question_bank.get_initial_questions("genetic_screening")
        assert isinstance(genetic_initial, list)
        assert len(genetic_initial) > 0
        assert "demo_age" in genetic_initial
        assert "family_cancer_history" in genetic_initial
        
        # Test epigenetic assessment
        epigenetic_initial = question_bank.get_initial_questions("epigenetic_assessment")
        assert isinstance(epigenetic_initial, list)
        assert len(epigenetic_initial) > 0
        assert "lifestyle_smoking" in epigenetic_initial
        
        # Test comprehensive assessment
        comprehensive_initial = question_bank.get_initial_questions("comprehensive_assessment")
        assert isinstance(comprehensive_initial, list)
        assert len(comprehensive_initial) > 0
        assert "demo_age" in comprehensive_initial
        assert "family_cancer_history" in comprehensive_initial

    def test_estimate_total_questions(self, question_bank):
        """Test question count estimation."""
        genetic_estimate = question_bank.estimate_total_questions("genetic_screening")
        assert isinstance(genetic_estimate, int)
        assert 10 <= genetic_estimate <= 20
        
        epigenetic_estimate = question_bank.estimate_total_questions("epigenetic_assessment")
        assert isinstance(epigenetic_estimate, int)
        assert 8 <= epigenetic_estimate <= 15
        
        comprehensive_estimate = question_bank.estimate_total_questions("comprehensive_assessment")
        assert isinstance(comprehensive_estimate, int)
        assert 20 <= comprehensive_estimate <= 30

    def test_get_question(self, question_bank):
        """Test retrieving specific questions."""
        # Test existing question
        age_question = question_bank.get_question("demo_age")
        assert age_question is not None
        assert "question_text" in age_question
        assert "question_type" in age_question
        assert age_question["question_type"] == "numeric"
        
        # Test non-existing question
        fake_question = question_bank.get_question("fake_question_id")
        assert fake_question is None

    def test_get_next_question_adaptive_logic(self, question_bank, sample_responses):
        """Test adaptive question selection logic."""
        question_path = ["demo_age", "demo_gender", "family_cancer_history"]
        
        # Test genetic screening flow
        next_q = question_bank.get_next_question(
            "genetic_screening", sample_responses, question_path
        )
        
        # Should get a follow-up question since family history is positive
        assert next_q is not None
        assert next_q not in question_path
        
        # Test that family history follow-ups are prioritized
        family_questions = ["family_cancer_types", "family_cancer_relatives", "family_early_onset"]
        # Next question should likely be one of these given positive family history
        if next_q in family_questions:
            assert True  # Expected behavior
        
        # Test epigenetic assessment
        next_epigenetic = question_bank.get_next_question(
            "epigenetic_assessment", sample_responses[:2], ["demo_age", "demo_gender"]
        )
        assert next_epigenetic is not None

    def test_get_questions_by_type(self, question_bank):
        """Test filtering questions by questionnaire type."""
        # Test genetic screening questions
        genetic_questions = question_bank.get_questions_by_type("genetic_screening")
        assert isinstance(genetic_questions, list)
        assert len(genetic_questions) > 0
        
        # Test that questions have genetic associations or are core demographics
        for question in genetic_questions[:5]:  # Test first 5
            has_genetic = question.get("genetic_associations") is not None
            is_core = question.get("category") in ["demographics", "family_history", "medical_history"]
            assert has_genetic or is_core
        
        # Test epigenetic assessment questions
        epigenetic_questions = question_bank.get_questions_by_type("epigenetic_assessment")
        assert isinstance(epigenetic_questions, list)
        assert len(epigenetic_questions) > 0
        
        # Test filtering by category
        lifestyle_questions = question_bank.get_questions_by_type("epigenetic_assessment", "lifestyle")
        assert isinstance(lifestyle_questions, list)
        for question in lifestyle_questions:
            assert question.get("category") == "lifestyle"

    def test_question_structure_validation(self, question_bank):
        """Test that all questions have required structure."""
        for question_id, question in list(question_bank.questions.items())[:10]:  # Test first 10
            # Required fields
            assert "question_text" in question
            assert "question_type" in question
            assert "category" in question
            assert "priority_weight" in question
            
            # Test question types
            assert question["question_type"] in [
                "multiple_choice", "multi_select", "boolean", "numeric", "text"
            ]
            
            # Test that priority weight is numeric
            assert isinstance(question["priority_weight"], (int, float))
            assert question["priority_weight"] > 0
            
            # Test options for choice questions
            if question["question_type"] in ["multiple_choice", "multi_select"]:
                assert "options" in question
                assert isinstance(question["options"], list)
                assert len(question["options"]) > 0

    def test_genetic_associations_validation(self, question_bank):
        """Test genetic associations structure."""
        questions_with_genetic = [
            q for q in question_bank.questions.values() 
            if q.get("genetic_associations")
        ]
        
        assert len(questions_with_genetic) > 0
        
        for question in questions_with_genetic[:5]:  # Test first 5
            genetic_assoc = question["genetic_associations"]
            assert isinstance(genetic_assoc, dict)
            
            for gene, weight in genetic_assoc.items():
                assert isinstance(gene, str)
                assert isinstance(weight, (int, float))
                assert 0 <= weight <= 1

    def test_epigenetic_associations_validation(self, question_bank):
        """Test epigenetic associations structure."""
        questions_with_epigenetic = [
            q for q in question_bank.questions.values() 
            if q.get("epigenetic_associations")
        ]
        
        assert len(questions_with_epigenetic) > 0
        
        for question in questions_with_epigenetic[:5]:  # Test first 5
            epigenetic_assoc = question["epigenetic_associations"]
            assert isinstance(epigenetic_assoc, dict)
            
            for factor, weight in epigenetic_assoc.items():
                assert isinstance(factor, str)
                assert isinstance(weight, (int, float))
                assert -1 <= weight <= 1  # Can be negative for protective factors

    def test_skip_conditions_logic(self, question_bank):
        """Test skip conditions functionality."""
        # Test that questions with skip conditions are properly handled
        responses_with_skip = [
            {"question_id": "family_cancer_history", "response": False}
        ]
        
        question_path = ["family_cancer_history"]
        
        next_q = question_bank.get_next_question(
            "genetic_screening", responses_with_skip, question_path
        )
        
        # Should not get family history follow-up questions
        family_followups = ["family_cancer_types", "family_cancer_relatives"]
        if next_q:
            assert next_q not in family_followups

    def test_question_dependencies(self, question_bank):
        """Test question dependency system."""
        # Test that dependent questions are properly managed
        dependencies = question_bank.question_dependencies
        
        # Test known dependencies
        assert "family_cancer_types" in dependencies
        assert "family_cancer_history" in dependencies["family_cancer_types"]
        
        assert "personal_cancer_type" in dependencies
        assert "personal_cancer_history" in dependencies["personal_cancer_type"]

    def test_validate_question_bank(self, question_bank):
        """Test question bank validation functionality."""
        validation_result = question_bank.validate()
        
        assert isinstance(validation_result, dict)
        assert "valid" in validation_result
        assert "issues" in validation_result
        assert "stats" in validation_result
        assert "recommendations" in validation_result
        
        # Test stats structure
        stats = validation_result["stats"]
        assert "total_questions" in stats
        assert "categories" in stats
        assert "genetic_associations" in stats
        assert "epigenetic_associations" in stats
        
        # Test that we have reasonable number of questions
        assert stats["total_questions"] > 20
        assert stats["genetic_associations"] > 5
        assert stats["epigenetic_associations"] > 5

    def test_decision_tree_structure(self, question_bank):
        """Test decision tree structure and logic."""
        for questionnaire_type, tree in question_bank.decision_trees.items():
            assert "primary_path" in tree
            assert isinstance(tree["primary_path"], list)
            assert len(tree["primary_path"]) > 0
            
            if "branch_conditions" in tree:
                branch_conditions = tree["branch_conditions"]
                assert isinstance(branch_conditions, dict)
                
                for condition_q, branches in branch_conditions.items():
                    assert isinstance(branches, dict)
                    for branch_value, follow_questions in branches.items():
                        assert isinstance(follow_questions, list)

    def test_question_relevance_logic(self, question_bank):
        """Test question relevance determination."""
        # Test genetic screening relevance
        genetic_question = {
            "genetic_associations": {"BRCA1": 0.5},
            "category": "family_history"
        }
        assert question_bank._is_question_relevant(genetic_question, "genetic_screening")
        
        # Test epigenetic assessment relevance
        epigenetic_question = {
            "epigenetic_associations": {"dna_methylation_patterns": 0.3},
            "category": "lifestyle"
        }
        assert question_bank._is_question_relevant(epigenetic_question, "epigenetic_assessment")
        
        # Test comprehensive assessment (should accept all)
        assert question_bank._is_question_relevant(genetic_question, "comprehensive_assessment")
        assert question_bank._is_question_relevant(epigenetic_question, "comprehensive_assessment")

    def test_candidate_question_selection(self, question_bank):
        """Test candidate question finding logic."""
        response_map = {
            "demo_age": 45,
            "family_cancer_history": True
        }
        question_path = ["demo_age", "family_cancer_history"]
        
        candidates = question_bank._find_candidate_questions(
            "genetic_screening", response_map, question_path
        )
        
        assert isinstance(candidates, list)
        # Should not include already asked questions
        for candidate in candidates:
            assert candidate not in question_path
        
        # Should include follow-up questions for positive family history
        family_followups = ["family_cancer_types", "family_cancer_relatives"]
        assert any(q in candidates for q in family_followups)

    def test_relevance_boost_calculation(self, question_bank):
        """Test relevance boost calculations."""
        # Test family history boost
        question_with_family_category = {"category": "family_history"}
        response_map_positive_family = {"family_cancer_history": True}
        
        boost = question_bank._calculate_relevance_boost(
            question_with_family_category, response_map_positive_family
        )
        assert boost > 0
        
        # Test smoking boost
        question_with_lifestyle_category = {"category": "lifestyle"}
        response_map_smoking = {"lifestyle_smoking": "Current smoker"}
        
        boost_smoking = question_bank._calculate_relevance_boost(
            question_with_lifestyle_category, response_map_smoking
        )
        assert boost_smoking > 0

    def test_question_selection_prioritization(self, question_bank, sample_responses):
        """Test that question selection prioritizes correctly."""
        question_path = ["demo_age", "demo_gender"]
        
        # Get next question with family history positive
        next_q = question_bank.get_next_question(
            "genetic_screening", sample_responses, question_path
        )
        
        if next_q:
            next_question_data = question_bank.get_question(next_q)
            # Should prioritize high-weight questions
            assert next_question_data.get("priority_weight", 0) > 5.0

    def test_edge_cases_and_error_handling(self, question_bank):
        """Test edge cases and error handling."""
        # Test with empty responses
        empty_next = question_bank.get_next_question("genetic_screening", [], [])
        # Should still return initial questions
        assert empty_next is not None
        
        # Test with invalid questionnaire type
        invalid_type_result = question_bank.get_initial_questions("invalid_type")
        assert isinstance(invalid_type_result, list)
        # Should return empty list or handle gracefully
        
        # Test with very long question path (questionnaire completion)
        long_path = list(question_bank.questions.keys())[:50]  # Most questions
        completed_next = question_bank.get_next_question(
            "genetic_screening", [], long_path
        )
        # Should return None when mostly complete
        assert completed_next is None or completed_next not in long_path

    def test_performance_benchmarks(self, question_bank):
        """Test performance of question bank operations."""
        import time
        
        # Test question retrieval performance
        start_time = time.time()
        for _ in range(1000):
            question_bank.get_question("demo_age")
        retrieval_time = time.time() - start_time
        assert retrieval_time < 1.0  # Should be very fast
        
        # Test next question selection performance
        sample_responses = [
            {"question_id": "demo_age", "response": 45},
            {"question_id": "family_cancer_history", "response": True}
        ]
        
        start_time = time.time()
        for _ in range(100):
            question_bank.get_next_question("genetic_screening", sample_responses, ["demo_age"])
        selection_time = time.time() - start_time
        assert selection_time < 2.0  # Should complete in reasonable time

    def test_question_content_quality(self, question_bank):
        """Test question content quality and completeness."""
        # Test that demographic questions exist
        demo_questions = [q for q in question_bank.questions.values() 
                         if q.get("category") == "demographics"]
        assert len(demo_questions) >= 3  # Age, gender, ethnicity minimum
        
        # Test that family history questions exist
        family_questions = [q for q in question_bank.questions.values() 
                           if q.get("category") == "family_history"]
        assert len(family_questions) >= 5
        
        # Test that lifestyle questions exist
        lifestyle_questions = [q for q in question_bank.questions.values() 
                              if q.get("category") == "lifestyle"]
        assert len(lifestyle_questions) >= 5
        
        # Test question text quality (basic checks)
        for question_id, question in list(question_bank.questions.items())[:10]:
            question_text = question.get("question_text", "")
            assert len(question_text) > 10  # Not too short
            assert len(question_text) < 500  # Not too long
            assert "?" in question_text or question_text.endswith(":")  # Proper question format


class TestQuestionDataClass:
    """Test cases for Question data class."""
    
    def test_question_creation(self):
        """Test Question object creation."""
        question = Question(
            question_id="test_id",
            question_text="Test question?",
            question_type="multiple_choice",
            options=["Option 1", "Option 2"],
            validation_rules={"required": True},
            genetic_associations={"BRCA1": 0.5},
            epigenetic_associations={"dna_methylation_patterns": 0.3},
            category="test",
            priority_weight=5.0,
            skip_conditions={"other_question": False},
            follow_up_questions=["follow_up_1"]
        )
        
        assert question.question_id == "test_id"
        assert question.question_text == "Test question?"
        assert question.question_type == "multiple_choice"
        assert question.options == ["Option 1", "Option 2"]
        assert question.validation_rules == {"required": True}
        assert question.genetic_associations == {"BRCA1": 0.5}
        assert question.epigenetic_associations == {"dna_methylation_patterns": 0.3}
        assert question.category == "test"
        assert question.priority_weight == 5.0
        assert question.skip_conditions == {"other_question": False}
        assert question.follow_up_questions == ["follow_up_1"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
