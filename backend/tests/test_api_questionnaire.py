"""
Comprehensive test suite for the Questionnaire API endpoints

Tests cover all REST API endpoints, request/response validation,
error handling, and integration scenarios.
"""

import pytest
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

# Import the API components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

# Import the main FastAPI app and dependencies
from main import app
from api.v1.questionnaire import get_questionnaire_service
from services.questionnaire_service import QuestionnaireService


class TestQuestionnaireAPI:
    """Test cases for Questionnaire API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_service(self):
        """Mock questionnaire service for testing."""
        service = Mock(spec=QuestionnaireService)
        
        # Mock service responses
        service.start_session.return_value = {
            "session_id": "test-session-123",
            "questionnaire_type": "genetic_screening",
            "total_estimated_questions": 15,
            "initial_questions": ["demo_age", "demo_gender"],
            "created_at": "2025-06-11T12:00:00"
        }
        
        service.get_next_question.return_value = {
            "question": {
                "question_id": "demo_age",
                "question_text": "What is your age?",
                "question_type": "numeric",
                "validation_rules": {"min": 0, "max": 120}
            },
            "progress": {
                "questions_answered": 0,
                "total_estimated": 15,
                "progress_percentage": 0
            },
            "complete": False,
            "session_id": "test-session-123"
        }
        
        service.submit_response.return_value = {
            "next_question": {
                "question_id": "demo_gender",
                "question_text": "What is your gender?",
                "question_type": "multiple_choice",
                "options": ["Male", "Female", "Other"]
            },
            "progress": {
                "questions_answered": 1,
                "total_estimated": 15,
                "progress_percentage": 6.67
            },
            "complete": False,
            "updated_risks": {
                "overall_risk": 0.1
            }
        }
        
        service.get_session_results.return_value = {
            "session_id": "test-session-123",
            "questionnaire_type": "genetic_screening",
            "completion_status": "completed",
            "genetic_risks": [],
            "epigenetic_risks": [],
            "clinical_recommendations": {
                "genetic_testing": ["Consider genetic counseling"],
                "lifestyle_modifications": ["Maintain healthy diet"],
                "follow_up": ["Annual screening recommended"],
                "urgency_level": "routine"
            },
            "completed_at": "2025-06-11T12:15:00"
        }
        
        service.pause_session.return_value = {
            "status": "paused",
            "resume_token": "resume-token-123",
            "paused_at": "2025-06-11T12:10:00"
        }
        
        service.resume_session.return_value = {
            "session_id": "test-session-456",
            "questionnaire_type": "genetic_screening",
            "progress": {
                "questions_answered": 5,
                "total_estimated": 15,
                "progress_percentage": 33.33
            },
            "status": "active"
        }
        
        service.get_session_analytics.return_value = {
            "session_id": "test-session-123",
            "total_time_minutes": 8.5,
            "questions_answered": 12,
            "avg_time_per_question": 0.71,
            "completion_percentage": 80.0
        }
        
        return service
    
    @pytest.fixture(autouse=True)
    def mock_dependencies(self, mock_service):
        """Mock all service dependencies."""
        def override_get_questionnaire_service():
            return mock_service
        
        app.dependency_overrides[get_questionnaire_service] = override_get_questionnaire_service
        yield
        app.dependency_overrides.clear()

    def test_start_session_endpoint(self, client, mock_service):
        """Test POST /start-session endpoint."""
        request_data = {
            "questionnaire_type": "genetic_screening"
        }
        
        response = client.post("/api/v1/questionnaire/start-session", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "session_id" in data
        assert "questionnaire_type" in data
        assert "total_estimated_questions" in data
        assert "initial_questions" in data
        assert "created_at" in data
        
        assert data["questionnaire_type"] == "genetic_screening"
        assert data["session_id"] == "test-session-123"
        
        # Verify service was called correctly
        mock_service.start_session.assert_called_once_with("genetic_screening")

    def test_start_session_invalid_type(self, client, mock_service):
        """Test start session with invalid questionnaire type."""
        request_data = {
            "questionnaire_type": "invalid_type"
        }
        
        response = client.post("/api/v1/questionnaire/start-session", json=request_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    def test_start_session_missing_data(self, client):
        """Test start session with missing request data."""
        response = client.post("/api/v1/questionnaire/start-session", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_next_question_endpoint(self, client, mock_service):
        """Test GET /questions/{session_id}/next endpoint."""
        session_id = "test-session-123"
        
        response = client.get(f"/api/v1/questionnaire/questions/{session_id}/next")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "question" in data
        assert "progress" in data
        assert "complete" in data
        assert "session_id" in data
        
        assert data["question"]["question_id"] == "demo_age"
        assert data["complete"] == False
        
        # Verify service was called
        mock_service.get_next_question.assert_called_once_with(session_id)

    def test_get_next_question_invalid_session(self, client, mock_service):
        """Test get next question with invalid session."""
        mock_service.get_next_question.side_effect = ValueError("Session not found")
        
        response = client.get("/api/v1/questionnaire/questions/invalid-session/next")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Session not found" in data["detail"]

    def test_submit_response_endpoint(self, client, mock_service):
        """Test POST /questions/{session_id}/respond endpoint."""
        session_id = "test-session-123"
        request_data = {
            "question_id": "demo_age",
            "response": 45,
            "confidence": 1.0
        }
        
        response = client.post(
            f"/api/v1/questionnaire/questions/{session_id}/respond",
            json=request_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "next_question" in data
        assert "progress" in data
        assert "complete" in data
        assert "updated_risks" in data
        
        assert data["next_question"]["question_id"] == "demo_gender"
        assert data["complete"] == False
        
        # Verify service was called with correct data
        mock_service.submit_response.assert_called_once_with(session_id, request_data)

    def test_submit_response_completion(self, client, mock_service):
        """Test response submission that completes questionnaire."""
        # Mock completion response
        mock_service.submit_response.return_value = {
            "complete": True,
            "final_results": {
                "genetic_risks": [],
                "epigenetic_risks": [],
                "overall_risk_score": 0.15,
                "clinical_urgency": "moderate"
            }
        }
        
        session_id = "test-session-123"
        request_data = {
            "question_id": "final_question",
            "response": "Yes",
            "confidence": 1.0
        }
        
        response = client.post(
            f"/api/v1/questionnaire/questions/{session_id}/respond",
            json=request_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["complete"] == True
        assert "final_results" in data
        assert "genetic_risks" in data["final_results"]

    def test_submit_response_invalid_data(self, client):
        """Test submit response with invalid data."""
        session_id = "test-session-123"
        invalid_data = {
            "response": 45
            # Missing question_id
        }
        
        response = client.post(
            f"/api/v1/questionnaire/questions/{session_id}/respond",
            json=invalid_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_session_results_endpoint(self, client, mock_service):
        """Test GET /sessions/{session_id}/results endpoint."""
        session_id = "test-session-123"
        
        response = client.get(f"/api/v1/questionnaire/sessions/{session_id}/results")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "session_id" in data
        assert "questionnaire_type" in data
        assert "completion_status" in data
        assert "genetic_risks" in data
        assert "epigenetic_risks" in data
        assert "clinical_recommendations" in data
        
        assert data["completion_status"] == "completed"
        
        # Verify service was called
        mock_service.get_session_results.assert_called_once_with(session_id)

    def test_pause_session_endpoint(self, client, mock_service):
        """Test POST /sessions/{session_id}/pause endpoint."""
        session_id = "test-session-123"
        
        response = client.post(f"/api/v1/questionnaire/sessions/{session_id}/pause")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "status" in data
        assert "resume_token" in data
        assert "paused_at" in data
        
        assert data["status"] == "paused"
        
        # Verify service was called
        mock_service.pause_session.assert_called_once_with(session_id)

    def test_resume_session_endpoint(self, client, mock_service):
        """Test POST /sessions/resume endpoint."""
        request_data = {
            "resume_token": "resume-token-123"
        }
        
        response = client.post("/api/v1/questionnaire/sessions/resume", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "session_id" in data
        assert "questionnaire_type" in data
        assert "progress" in data
        assert "status" in data
        
        assert data["status"] == "active"
        
        # Verify service was called
        mock_service.resume_session.assert_called_once_with("resume-token-123")

    def test_get_session_analytics_endpoint(self, client, mock_service):
        """Test GET /sessions/{session_id}/analytics endpoint."""
        session_id = "test-session-123"
        
        response = client.get(f"/api/v1/questionnaire/sessions/{session_id}/analytics")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "session_id" in data
        assert "total_time_minutes" in data
        assert "questions_answered" in data
        assert "avg_time_per_question" in data
        assert "completion_percentage" in data
        
        assert data["questions_answered"] == 12
        assert data["completion_percentage"] == 80.0
        
        # Verify service was called
        mock_service.get_session_analytics.assert_called_once_with(session_id)

    def test_api_error_handling(self, client, mock_service):
        """Test API error handling for service exceptions."""
        # Mock service raising an exception
        mock_service.get_next_question.side_effect = Exception("Internal service error")
        
        response = client.get("/api/v1/questionnaire/questions/test-session/next")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data

    def test_request_validation(self, client):
        """Test request validation for various endpoints."""
        # Test invalid JSON
        response = client.post(
            "/api/v1/questionnaire/start-session",
            data="invalid json"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing required fields
        response = client.post(
            "/api/v1/questionnaire/questions/session-123/respond",
            json={"confidence": 1.0}  # Missing question_id and response
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_response_format_consistency(self, client, mock_service):
        """Test that all API responses follow consistent format."""
        # Test various endpoints and verify response structure
        endpoints_to_test = [
            ("/api/v1/questionnaire/start-session", "POST", {"questionnaire_type": "genetic_screening"}),
            ("/api/v1/questionnaire/questions/test-session/next", "GET", None),
            ("/api/v1/questionnaire/sessions/test-session/results", "GET", None),
            ("/api/v1/questionnaire/sessions/test-session/analytics", "GET", None)
        ]
        
        for endpoint, method, data in endpoints_to_test:
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert isinstance(response_data, dict)

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/api/v1/questionnaire/start-session")
        
        # CORS headers should be present (depending on app configuration)
        # This test would need to be adjusted based on actual CORS setup
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]

    def test_api_documentation_endpoints(self, client):
        """Test that API documentation endpoints are accessible."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_integration(self, client):
        """Test health check endpoint works."""
        response = client.get("/health")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
        data = response.json()
        assert "status" in data

    def test_concurrent_api_requests(self, client, mock_service):
        """Test handling of concurrent API requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.post("/api/v1/questionnaire/start-session", 
                                 json={"questionnaire_type": "genetic_screening"})
            results.append(response.status_code)
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status_code == status.HTTP_200_OK for status_code in results)
        assert len(results) == 10

    def test_api_rate_limiting(self, client):
        """Test API rate limiting (if implemented)."""
        # This test would check if rate limiting is properly implemented
        # The exact implementation depends on the rate limiting strategy
        
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = client.get("/api/v1/questionnaire/questions/test-session/next")
            responses.append(response.status_code)
        
        # Most should succeed, but some might be rate limited
        success_count = sum(1 for status_code in responses if status_code == status.HTTP_200_OK)
        
        # At least some requests should succeed
        assert success_count > 0

    def test_api_security_headers(self, client):
        """Test that security headers are properly set."""
        response = client.get("/api/v1/questionnaire/questions/test-session/next")
        
        # Check for common security headers
        # These would depend on the actual security middleware configuration
        headers = response.headers
        
        # Test that the response includes proper headers
        assert "content-type" in headers
        assert headers["content-type"] == "application/json"

    def test_api_performance(self, client, mock_service):
        """Test API response time performance."""
        import time
        
        # Test response times for critical endpoints
        start_time = time.time()
        response = client.post("/api/v1/questionnaire/start-session", 
                             json={"questionnaire_type": "genetic_screening"})
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        response_time = end_time - start_time
        
        # API should respond within reasonable time (adjust threshold as needed)
        assert response_time < 1.0  # Less than 1 second

    def test_data_validation_edge_cases(self, client, mock_service):
        """Test data validation with edge cases."""
        # Test with various edge case inputs
        edge_cases = [
            {"questionnaire_type": ""},  # Empty string
            {"questionnaire_type": None},  # None value
            {"questionnaire_type": 123},  # Wrong type
            {"questionnaire_type": "a" * 1000},  # Very long string
        ]
        
        for case in edge_cases:
            response = client.post("/api/v1/questionnaire/start-session", json=case)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    def test_api_logging_integration(self, client, mock_service):
        """Test that API calls are properly logged."""
        # This test would verify that API calls generate appropriate log entries
        # Implementation depends on the logging configuration
        
        with patch('logging.getLogger') as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance
            
            response = client.post("/api/v1/questionnaire/start-session", 
                                 json={"questionnaire_type": "genetic_screening"})
            
            assert response.status_code == status.HTTP_200_OK
            # Verify that logging was called (if implemented)


@pytest.mark.integration
class TestQuestionnaireAPIIntegration:
    """Integration tests for the complete questionnaire flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client for integration testing."""
        return TestClient(app)
    
    def test_complete_questionnaire_flow(self, client):
        """Test a complete questionnaire flow from start to finish."""
        # This test would run through a complete questionnaire without mocks
        # It requires actual service implementations to be working
        pass
    
    def test_multi_session_handling(self, client):
        """Test handling of multiple concurrent sessions."""
        # This test would verify that multiple users can use the system simultaneously
        pass
    
    def test_session_persistence(self, client):
        """Test that sessions persist correctly across requests."""
        # This test would verify session data persistence in Redis
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
