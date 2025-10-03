#!/usr/bin/env python
"""
Comprehensive API Test Script for Trojan Defender Backend
Tests all endpoints systematically to ensure complete functionality
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# Obtain JWT dynamically (fallback to env TEST_JWT_TOKEN if provided)
JWT_TOKEN = os.environ.get("TEST_JWT_TOKEN")
if not JWT_TOKEN:
    try:
        from get_token import get_token as obtain_token
        JWT_TOKEN = obtain_token()
    except Exception as e:
        print(f"⚠️ Failed to import or obtain JWT token automatically: {e}")
        JWT_TOKEN = None

class APITester:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json"
        }
        if JWT_TOKEN:
            self.headers["Authorization"] = f"Bearer {JWT_TOKEN}"
        self.results = []
        self.passed = 0
        self.failed = 0
        # lazy importer for token refresh to avoid import cost if not needed
        self._obtain_token_fn = None

    def _ensure_token(self):
        """Ensure we have a valid JWT token, obtain if missing."""
        global JWT_TOKEN
        if not JWT_TOKEN:
            try:
                if self._obtain_token_fn is None:
                    from get_token import get_token as obtain_token
                    self._obtain_token_fn = obtain_token
                JWT_TOKEN = self._obtain_token_fn()
                if JWT_TOKEN:
                    self.headers["Authorization"] = f"Bearer {JWT_TOKEN}"
            except Exception as e:
                print(f"⚠️ Could not obtain JWT token: {e}")

    def _retry_with_fresh_token(self, endpoint, method, data, expected_codes):
        """Retry the request once after fetching a fresh token (for 401 cases)."""
        self._ensure_token()
        if "Authorization" not in self.headers:
            return None
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                return requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                return requests.post(url, json=data, headers=self.headers, timeout=10)
            elif method == "PUT":
                return requests.put(url, json=data, headers=self.headers, timeout=10)
            elif method == "DELETE":
                return requests.delete(url, headers=self.headers, timeout=10)
        except Exception:
            return None

    def log_result(self, endpoint, method, status_code, expected_codes, response_text="", error=None):
        """Log test result"""
        success = status_code in expected_codes
        if success:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
            
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "expected": expected_codes,
            "success": success,
            "error": str(error) if error else None,
            "response": response_text[:200] if response_text else ""
        }
        self.results.append(result)
        
        print(f"{status} {method} {endpoint} - Status: {status_code} (Expected: {expected_codes})")
        if error:
            print(f"    Error: {error}")
        if response_text and len(response_text) > 200:
            print(f"    Response: {response_text[:200]}...")
        elif response_text:
            print(f"    Response: {response_text}")
        print()
        
    def test_endpoint(self, endpoint, method="GET", data=None, expected_codes=[200], use_auth=True):
        """Test a single endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}

        # Ensure token for authenticated requests
        if use_auth:
            if "Authorization" not in self.headers:
                self._ensure_token()
            if "Authorization" in self.headers:
                headers.update(self.headers)

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)

            # If we hit 401 on an authenticated endpoint, try once with a fresh token
            if use_auth and response.status_code == 401:
                retry_resp = self._retry_with_fresh_token(endpoint, method, data, expected_codes)
                if retry_resp is not None:
                    response = retry_resp
            
            # Try to get response text
            try:
                response_text = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                if isinstance(response_text, dict):
                    response_text = json.dumps(response_text, indent=2)
            except Exception:
                response_text = response.text
                
            self.log_result(endpoint, method, response.status_code, expected_codes, response_text)
            return response
            
        except Exception as e:
            self.log_result(endpoint, method, 0, expected_codes, error=e)
            return None
    
    def test_authentication_endpoints(self):
        """Test authentication related endpoints"""
        print("🔐 Testing Authentication Endpoints")
        print("=" * 50)
        
        # Test login endpoint
        login_data = {
            "email": "admin@example.com",
            "password": "admin123"
        }
        self.test_endpoint("/api/auth/login/", "POST", login_data, [200], use_auth=False)
        
        # Test alternative login endpoint
        self.test_endpoint("/api/auth/token/", "POST", login_data, [200], use_auth=False)
        
        # Test profile endpoint (requires auth)
        self.test_endpoint("/api/auth/profile/", "GET", expected_codes=[200])
        
        # Test registration endpoint
        register_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        self.test_endpoint("/api/auth/register/", "POST", register_data, [201, 400], use_auth=False)
        
    def test_scanner_endpoints(self):
        """Test scanner related endpoints"""
        print("🔍 Testing Scanner Endpoints")
        print("=" * 50)
        
        # Test scanner endpoints
        self.test_endpoint("/api/scanner/", "GET", expected_codes=[200])
        self.test_endpoint("/api/scanner/results/", "GET", expected_codes=[200])
        self.test_endpoint("/api/scanner/statistics/", "GET", expected_codes=[200])
        self.test_endpoint("/api/scanner/stats/", "GET", expected_codes=[200])
        self.test_endpoint("/api/scanner/yara-rules/", "GET", expected_codes=[200])
        
    def test_threat_intelligence_endpoints(self):
        """Test threat intelligence endpoints"""
        print("🛡️ Testing Threat Intelligence Endpoints")
        print("=" * 50)
        
        # Test threat intelligence endpoints
        self.test_endpoint("/api/threat-intelligence/", "GET", expected_codes=[200, 404])
        self.test_endpoint("/api/threat-intelligence/threats/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threat-intelligence/events/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threat-intelligence/dashboard/stats/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threat-intelligence/map/data/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threat-intelligence/statistics/", "GET", expected_codes=[200])
        
        # Test threat intelligence update (this was failing before)
        update_data = {"force_update": True}
        self.test_endpoint("/api/threat-intelligence/update/", "POST", update_data, [200, 202])
        
        # Test IP checking
        ip_data = {"ips": ["8.8.8.8", "1.1.1.1"]}
        self.test_endpoint("/api/threat-intelligence/check-ips/", "POST", ip_data, [200])
        
    def test_threatmap_endpoints(self):
        """Test threat map endpoints"""
        print("🗺️ Testing Threat Map Endpoints")
        print("=" * 50)
        
        self.test_endpoint("/api/threatmap/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threatmap/events/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threatmap/map/", "GET", expected_codes=[200])
        self.test_endpoint("/api/threatmap/stats/", "GET", expected_codes=[200])
        
    def test_notifications_endpoints(self):
        """Test notifications endpoints"""
        print("🔔 Testing Notifications Endpoints")
        print("=" * 50)
        
        self.test_endpoint("/api/notifications/", "GET", expected_codes=[200])
        self.test_endpoint("/api/auth/notifications/preferences/", "GET", expected_codes=[200])
        self.test_endpoint("/api/auth/notifications/actions/", "GET", expected_codes=[200])
        
    def test_api_documentation(self):
        """Test API documentation endpoints"""
        print("📚 Testing API Documentation")
        print("=" * 50)
        
        self.test_endpoint("/swagger/", "GET", expected_codes=[200], use_auth=False)
        self.test_endpoint("/redoc/", "GET", expected_codes=[200], use_auth=False)
        self.test_endpoint("/swagger.json", "GET", expected_codes=[200], use_auth=False)
        
    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("🌐 Testing Basic Endpoints")
        print("=" * 50)
        
        self.test_endpoint("/api/", "GET", expected_codes=[200], use_auth=False)
        self.test_endpoint("/", "GET", expected_codes=[200], use_auth=False)
        
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Comprehensive API Tests at {datetime.now()}")
        token_preview = JWT_TOKEN[:50] + "..." if JWT_TOKEN else "<none>"
        print(f"🔑 Using JWT Token: {token_preview}")
        print("=" * 80)
        
        # Run all test suites
        self.test_basic_endpoints()
        self.test_authentication_endpoints()
        self.test_scanner_endpoints()
        self.test_threat_intelligence_endpoints()
        self.test_threatmap_endpoints()
        self.test_notifications_endpoints()
        self.test_api_documentation()
        
        # Print summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        total = (self.passed + self.failed) or 1
        print(f"📈 Success Rate: {(self.passed / total * 100):.1f}%")
        
        # Print failed tests
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            print("-" * 40)
            for result in self.results:
                if not result["success"]:
                    print(f"{result['method']} {result['endpoint']} - Status: {result['status_code']} (Expected: {result['expected']})")
                    if result["error"]:
                        print(f"    Error: {result['error']}")
        
        print(f"\n🏁 Tests completed at {datetime.now()}")
        return self.passed, self.failed

if __name__ == "__main__":
    tester = APITester()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if tests failed
    exit(0 if failed == 0 else 1)