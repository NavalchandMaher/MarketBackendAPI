"""
End-to-End Authentication Flow Test
Market AI V3 Backend

This script tests the complete authentication flow:
1. Register user
2. Login
3. Access protected endpoints
4. Refresh token
5. Logout
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:10000"
TEST_USER_EMAIL = f"test_auth_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"
TEST_USER_NAME = "Test Auth User"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{title.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")

def print_response(response, title="Response"):
    """Pretty print API response"""
    print(f"\n{YELLOW}{title}:{RESET}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, default=str))
    except:
        print(response.text)
    print()

# Test 1: Register User
def test_register():
    """Test user registration"""
    print_section("TEST 1: User Registration")
    
    payload = {
        "full_name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "mobile_number": "+1234567890",
        "default_symbol": "BTCUSDT",
        "default_timeframe": "5m",
        "theme": "dark"
    }
    
    print_info(f"Registering user: {TEST_USER_EMAIL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    print_response(response, "Registration Response")
    
    if response.status_code == 201:
        print_success(f"User registered successfully (Status: {response.status_code})")
        return True
    else:
        print_error(f"User registration failed (Status: {response.status_code})")
        return False

# Test 2: Login User
def test_login():
    """Test user login and get tokens"""
    print_section("TEST 2: User Login")
    
    payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    print_info(f"Logging in user: {TEST_USER_EMAIL}")
    
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    
    print_response(response, "Login Response")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        user = data.get("user", {})
        
        print_success(f"User logged in successfully (Status: {response.status_code})")
        print_info(f"Access Token: {access_token[:50]}...")
        print_info(f"Refresh Token: {refresh_token[:50]}...")
        print_info(f"User ID: {user.get('id')}")
        print_info(f"User Email: {user.get('email')}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }
    else:
        print_error(f"User login failed (Status: {response.status_code})")
        return None

# Test 3: Access Protected Endpoint - Get User Profile
def test_get_user_profile(tokens):
    """Test accessing protected endpoint: GET /users/me"""
    print_section("TEST 3: Access Protected Endpoint - GET /users/me")
    
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    
    print_info("Accessing GET /users/me with access token")
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    print_response(response, "GET /users/me Response")
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Protected endpoint accessed successfully (Status: {response.status_code})")
        print_info(f"User: {data.get('email')}")
        print_info(f"Full Name: {data.get('full_name')}")
        print_info(f"Role: {data.get('role')}")
        return True
    else:
        print_error(f"Protected endpoint access failed (Status: {response.status_code})")
        return False

# Test 4: Access Protected Endpoint - Get Dashboard
def test_get_dashboard(tokens):
    """Test accessing protected endpoint: GET /v3/dashboard"""
    print_section("TEST 4: Access Protected Endpoint - GET /v3/dashboard")
    
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    
    print_info("Accessing GET /v3/dashboard with access token")
    
    response = requests.get(f"{BASE_URL}/v3/dashboard", headers=headers)
    
    print_response(response, "GET /v3/dashboard Response")
    
    if response.status_code == 200:
        print_success(f"Dashboard endpoint accessed successfully (Status: {response.status_code})")
        return True
    else:
        print_error(f"Dashboard endpoint access failed (Status: {response.status_code})")
        return False

# Test 5: Refresh Token
def test_refresh_token(tokens):
    """Test token refresh"""
    print_section("TEST 5: Token Refresh")
    
    payload = {
        "refresh_token": tokens['refresh_token']
    }
    
    print_info("Refreshing access token")
    
    response = requests.post(f"{BASE_URL}/auth/refresh", json=payload)
    
    print_response(response, "Token Refresh Response")
    
    if response.status_code == 200:
        data = response.json()
        new_access_token = data.get("access_token")
        
        print_success(f"Token refreshed successfully (Status: {response.status_code})")
        print_info(f"New Access Token: {new_access_token[:50]}...")
        
        tokens['access_token'] = new_access_token
        return tokens
    else:
        print_error(f"Token refresh failed (Status: {response.status_code})")
        return None

# Test 6: Access Protected Endpoint with Refreshed Token
def test_access_with_refreshed_token(tokens):
    """Test accessing protected endpoint with refreshed token"""
    print_section("TEST 6: Access Protected Endpoint with Refreshed Token")
    
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    
    print_info("Accessing GET /v3/strategies with refreshed access token")
    
    response = requests.get(f"{BASE_URL}/v3/strategies", headers=headers)
    
    print_response(response, "GET /v3/strategies Response")
    
    if response.status_code == 200:
        print_success(f"Protected endpoint accessed with refreshed token (Status: {response.status_code})")
        return True
    else:
        print_error(f"Protected endpoint access with refreshed token failed (Status: {response.status_code})")
        return False

# Test 7: Logout
def test_logout(tokens):
    """Test logout"""
    print_section("TEST 7: User Logout")
    
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    
    print_info("Logging out user")
    
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    
    print_response(response, "Logout Response")
    
    if response.status_code == 200:
        print_success(f"User logged out successfully (Status: {response.status_code})")
        return True
    else:
        print_error(f"User logout failed (Status: {response.status_code})")
        return False

# Test 8: Verify Token Invalid After Logout
def test_token_after_logout(tokens):
    """Test that token is invalid after logout"""
    print_section("TEST 8: Verify Token Invalid After Logout")
    
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    
    print_info("Attempting to access protected endpoint with logged-out token")
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    print_response(response, "Protected Endpoint Response")
    
    if response.status_code == 401 or response.status_code == 403:
        print_success(f"Access correctly denied after logout (Status: {response.status_code})")
        return True
    elif response.status_code == 200:
        print_error(f"Token should be invalid after logout but still works (Status: {response.status_code})")
        return False
    else:
        print_error(f"Unexpected status code (Status: {response.status_code})")
        return False

# Test 9: Test Invalid Credentials
def test_invalid_credentials():
    """Test login with invalid credentials"""
    print_section("TEST 9: Login with Invalid Credentials")
    
    payload = {
        "email": TEST_USER_EMAIL,
        "password": "WrongPassword123!"
    }
    
    print_info("Attempting login with wrong password")
    
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    
    print_response(response, "Login Response")
    
    if response.status_code == 401:
        print_success(f"Invalid credentials correctly rejected (Status: {response.status_code})")
        return True
    else:
        print_error(f"Expected 401 but got {response.status_code}")
        return False

# Test 10: Test Missing Authorization Header
def test_missing_auth_header():
    """Test accessing protected endpoint without authorization header"""
    print_section("TEST 10: Access Protected Endpoint Without Authorization Header")
    
    print_info("Attempting to access protected endpoint without token")
    
    response = requests.get(f"{BASE_URL}/users/me")
    
    print_response(response, "Protected Endpoint Response")
    
    if response.status_code == 403:
        print_success(f"Access correctly denied without token (Status: {response.status_code})")
        return True
    else:
        print_error(f"Expected 403 but got {response.status_code}")
        return False

# Main test runner
def main():
    """Run all authentication flow tests"""
    print(f"\n{BLUE}")
    print("╔" + "="*78 + "╗")
    print("║" + "END-TO-END AUTHENTICATION FLOW TEST".center(78) + "║")
    print("║" + "Market AI V3 Backend".center(78) + "║")
    print("║" + datetime.now().strftime("%Y-%m-%d %H:%M:%S").center(78) + "║")
    print("╚" + "="*78 + "╝")
    print(f"{RESET}\n")
    
    results = {}
    
    # Test 1: Register
    results["1_register"] = test_register()
    if not results["1_register"]:
        print_error("Registration failed, cannot continue tests")
        return results
    
    time.sleep(1)
    
    # Test 2: Login
    tokens = test_login()
    if not tokens:
        print_error("Login failed, cannot continue tests")
        return results
    results["2_login"] = True
    
    time.sleep(1)
    
    # Test 3: Get User Profile
    results["3_get_user_profile"] = test_get_user_profile(tokens)
    
    time.sleep(1)
    
    # Test 4: Get Dashboard
    results["4_get_dashboard"] = test_get_dashboard(tokens)
    
    time.sleep(1)
    
    # Test 5: Refresh Token
    refreshed_tokens = test_refresh_token(tokens)
    results["5_refresh_token"] = refreshed_tokens is not None
    if refreshed_tokens:
        tokens = refreshed_tokens
    
    time.sleep(1)
    
    # Test 6: Access with Refreshed Token
    results["6_access_with_refreshed_token"] = test_access_with_refreshed_token(tokens)
    
    time.sleep(1)
    
    # Test 7: Logout
    results["7_logout"] = test_logout(tokens)
    
    time.sleep(1)
    
    # Test 8: Token Invalid After Logout
    results["8_token_after_logout"] = test_token_after_logout(tokens)
    
    time.sleep(1)
    
    # Test 9: Invalid Credentials
    results["9_invalid_credentials"] = test_invalid_credentials()
    
    time.sleep(1)
    
    # Test 10: Missing Auth Header
    results["10_missing_auth_header"] = test_missing_auth_header()
    
    # Print Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"{BLUE}Results:{RESET}")
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name:.<50} {status}")
    
    print(f"\n{BLUE}Overall:{RESET}")
    print(f"  Passed: {GREEN}{passed}{RESET}/{total}")
    print(f"  Failed: {RED}{total - passed}{RESET}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All tests passed!{RESET}\n")
    else:
        print(f"\n{RED}✗ Some tests failed{RESET}\n")
    
    return results

if __name__ == "__main__":
    main()
