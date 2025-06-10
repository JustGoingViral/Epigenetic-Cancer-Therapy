#!/usr/bin/env python3
"""
MTET Platform API Test Script

This script tests the basic functionality of the MTET Platform API.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any


class MTETAPITester:
    """Test class for MTET Platform API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = f"Status: {data.get('status', 'unknown')}"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Health Check", success, message)
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_root_endpoint(self) -> bool:
        """Test root endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = f"API: {data.get('message', 'unknown')}"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Root Endpoint", success, message)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
            return False
    
    def test_api_info(self) -> bool:
        """Test API info endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/info")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = f"Version: {data.get('version', 'unknown')}"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("API Info", success, message)
            return success
        except Exception as e:
            self.log_test("API Info", False, str(e))
            return False
    
    def test_login(self, username: str = "admin", password: str = "admin123") -> bool:
        """Test user login."""
        try:
            login_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.access_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                message = "Login successful, token acquired"
            else:
                message = f"HTTP {response.status_code}"
                if response.status_code == 422:
                    message += " - Check if database is initialized"
            
            self.log_test("User Login", success, message)
            return success
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False
    
    def test_user_info(self) -> bool:
        """Test get current user info."""
        if not self.access_token:
            self.log_test("User Info", False, "No access token available")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/auth/me")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = f"User: {data.get('email', 'unknown')}"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("User Info", success, message)
            return success
        except Exception as e:
            self.log_test("User Info", False, str(e))
            return False
    
    def test_patients_endpoint(self) -> bool:
        """Test patients list endpoint."""
        if not self.access_token:
            self.log_test("Patients Endpoint", False, "No access token available")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/patients/")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = f"Patients: {len(data)} found"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Patients Endpoint", success, message)
            return success
        except Exception as e:
            self.log_test("Patients Endpoint", False, str(e))
            return False
    
    def test_openapi_docs(self) -> bool:
        """Test OpenAPI documentation endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/openapi.json")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = f"OpenAPI version: {data.get('openapi', 'unknown')}"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("OpenAPI Docs", success, message)
            return success
        except Exception as e:
            self.log_test("OpenAPI Docs", False, str(e))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("🧪 Running MTET Platform API Tests")
        print("=" * 50)
        
        # Basic connectivity tests
        basic_tests = [
            self.test_health_check(),
            self.test_root_endpoint(),
            self.test_api_info(),
            self.test_openapi_docs()
        ]
        
        # Authentication tests
        auth_tests = [
            self.test_login(),
            self.test_user_info()
        ]
        
        # Protected endpoint tests
        protected_tests = [
            self.test_patients_endpoint()
        ]
        
        # Calculate results
        all_tests = basic_tests + auth_tests + protected_tests
        passed = sum(all_tests)
        total = len(all_tests)
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the results above.")
            return False
    
    def save_results(self, filename: str = "test_results.json"):
        """Save test results to file."""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "base_url": self.base_url,
                    "results": self.test_results
                }, f, indent=2)
            print(f"📁 Test results saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MTET Platform API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API server"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save test results to file"
    )
    
    args = parser.parse_args()
    
    tester = MTETAPITester(args.url)
    
    try:
        success = tester.run_all_tests()
        
        if args.save_results:
            tester.save_results()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
