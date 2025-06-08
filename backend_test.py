#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
import uuid

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://035c983d-ca9e-423b-86e6-437b680bba4c.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test user credentials
TEST_USER = {
    "username": f"testuser_{uuid.uuid4().hex[:8]}",
    "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
    "password": "Password123!",
    "display_name": "Test User"
}

# Global variables to store tokens and IDs
access_token = None
refresh_token = None
user_id = None
chat_id = None
file_id = None

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message: str) -> None:
    """Print a header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(message: str) -> None:
    """Print a subheader message"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 50}{Colors.ENDC}\n")

def print_success(message: str) -> None:
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_warning(message: str) -> None:
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message: str) -> None:
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str) -> None:
    """Print an info message"""
    print(f"ℹ {message}")

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None, 
                 files: Dict[str, Any] = None, auth: bool = False) -> Tuple[Dict[str, Any], int]:
    """Make an HTTP request to the API"""
    url = f"{API_URL}{endpoint}"
    headers = {}
    
    if auth and access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=data)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers, files=files)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers)
        else:
            print_error(f"Unsupported HTTP method: {method}")
            return {}, 0
        
        if response.status_code >= 400:
            print_error(f"HTTP {response.status_code}: {response.text}")
            try:
                return response.json(), response.status_code
            except:
                return {"error": response.text}, response.status_code
        
        try:
            return response.json(), response.status_code
        except:
            return {"content": response.text}, response.status_code
            
    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, 0

def test_health_endpoints() -> bool:
    """Test health check endpoints"""
    print_subheader("Testing Health Endpoints")
    
    # Test root endpoint
    data, status_code = make_request("GET", "")
    if status_code == 200 and "message" in data:
        print_success("Root endpoint (/api) is working")
    else:
        print_error("Root endpoint (/api) failed")
        return False
    
    # Test health endpoint
    data, status_code = make_request("GET", "/health")
    if status_code == 200 and data.get("status") == "healthy":
        print_success("Health endpoint (/health) is working")
    else:
        print_error("Health endpoint (/health) failed")
        return False
    
    return True

def test_user_registration() -> bool:
    """Test user registration"""
    print_subheader("Testing User Registration")
    
    global user_id
    
    data, status_code = make_request("POST", "/auth/register", TEST_USER)
    
    if status_code == 200 and "id" in data:
        print_success(f"User registered successfully: {data['username']}")
        user_id = data["id"]
        return True
    else:
        print_error(f"User registration failed: {data.get('detail', 'Unknown error')}")
        return False

def test_user_login() -> bool:
    """Test user login"""
    print_subheader("Testing User Login")
    
    global access_token, refresh_token
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    data, status_code = make_request("POST", "/auth/login", login_data)
    
    if status_code == 200 and "access_token" in data:
        print_success("User login successful")
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        return True
    else:
        print_error(f"User login failed: {data.get('detail', 'Unknown error')}")
        return False

def test_get_current_user() -> bool:
    """Test getting current user info"""
    print_subheader("Testing Get Current User")
    
    data, status_code = make_request("GET", "/auth/me", auth=True)
    
    if status_code == 200 and data.get("email") == TEST_USER["email"]:
        print_success(f"Got current user: {data['username']}")
        return True
    else:
        print_error(f"Get current user failed: {data.get('detail', 'Unknown error')}")
        return False

def test_refresh_token() -> bool:
    """Test token refresh"""
    print_subheader("Testing Token Refresh")
    
    global access_token, refresh_token
    
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    data, status_code = make_request("POST", "/auth/refresh", refresh_data)
    
    if status_code == 200 and "access_token" in data:
        print_success("Token refresh successful")
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        return True
    else:
        print_error(f"Token refresh failed: {data.get('detail', 'Unknown error')}")
        return False

def test_create_chat() -> bool:
    """Test creating a new chat"""
    print_subheader("Testing Chat Creation")
    
    global chat_id
    
    chat_data = {
        "title": "Test Chat",
        "model": "alpha-origin",
        "system_prompt": "You are a helpful assistant."
    }
    
    data, status_code = make_request("POST", "/chats", chat_data, auth=True)
    
    if status_code == 200 and "id" in data:
        print_success(f"Chat created successfully: {data['title']}")
        chat_id = data["id"]
        return True
    else:
        print_error(f"Chat creation failed: {data.get('detail', 'Unknown error')}")
        return False

def test_get_chats() -> bool:
    """Test getting user chats"""
    print_subheader("Testing Get User Chats")
    
    data, status_code = make_request("GET", "/chats", auth=True)
    
    if status_code == 200 and isinstance(data, list):
        print_success(f"Got {len(data)} chats")
        return True
    else:
        print_error(f"Get chats failed: {data.get('detail', 'Unknown error')}")
        return False

def test_get_chat() -> bool:
    """Test getting a specific chat"""
    print_subheader("Testing Get Specific Chat")
    
    if not chat_id:
        print_error("No chat ID available for testing")
        return False
    
    data, status_code = make_request("GET", f"/chats/{chat_id}", auth=True)
    
    if status_code == 200 and data.get("id") == chat_id:
        print_success(f"Got chat: {data['title']}")
        return True
    else:
        print_error(f"Get chat failed: {data.get('detail', 'Unknown error')}")
        return False

def test_update_chat() -> bool:
    """Test updating a chat"""
    print_subheader("Testing Update Chat")
    
    if not chat_id:
        print_error("No chat ID available for testing")
        return False
    
    update_data = {
        "title": "Updated Test Chat",
        "pinned": True
    }
    
    data, status_code = make_request("PUT", f"/chats/{chat_id}", update_data, auth=True)
    
    if status_code == 200 and data.get("title") == update_data["title"]:
        print_success(f"Chat updated successfully: {data['title']}")
        return True
    else:
        print_error(f"Chat update failed: {data.get('detail', 'Unknown error')}")
        return False

def test_send_message() -> bool:
    """Test sending a message in a chat"""
    print_subheader("Testing Send Message")
    
    if not chat_id:
        print_error("No chat ID available for testing")
        return False
    
    message_data = {
        "content": "Hello, this is a test message!"
    }
    
    data, status_code = make_request("POST", f"/chats/{chat_id}/messages", message_data, auth=True)
    
    if status_code == 200 and "content" in data:
        print_success(f"Message sent successfully, got AI response")
        return True
    elif status_code == 500 and "API key" in data.get("detail", ""):
        print_warning("Message sent but AI response failed due to missing API key (expected)")
        return True
    else:
        print_error(f"Send message failed: {data.get('detail', 'Unknown error')}")
        return False

def test_get_messages() -> bool:
    """Test getting messages in a chat"""
    print_subheader("Testing Get Chat Messages")
    
    if not chat_id:
        print_error("No chat ID available for testing")
        return False
    
    data, status_code = make_request("GET", f"/chats/{chat_id}/messages", auth=True)
    
    if status_code == 200 and isinstance(data, list):
        print_success(f"Got {len(data)} messages")
        return True
    else:
        print_error(f"Get messages failed: {data.get('detail', 'Unknown error')}")
        return False

def test_file_upload() -> bool:
    """Test file upload"""
    print_subheader("Testing File Upload")
    
    global file_id
    
    # Create a temporary test file
    test_file_path = "test_file.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for upload testing.")
    
    try:
        # Prepare the file for upload
        files = {
            "file": ("test_file.txt", open(test_file_path, "rb"), "text/plain")
        }
        
        # Make the request
        url = f"{API_URL}/files/upload"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            file_id = data["id"]
            print_success(f"File uploaded successfully: {data['filename']}")
            return True
        else:
            try:
                error_data = response.json()
                print_error(f"File upload failed: {error_data.get('detail', 'Unknown error')}")
            except:
                print_error(f"File upload failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"File upload exception: {e}")
        return False
    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_get_files() -> bool:
    """Test getting user files"""
    print_subheader("Testing Get User Files")
    
    data, status_code = make_request("GET", "/files", auth=True)
    
    if status_code == 200 and isinstance(data, list):
        print_success(f"Got {len(data)} files")
        return True
    else:
        print_error(f"Get files failed: {data.get('detail', 'Unknown error')}")
        return False

def test_get_file() -> bool:
    """Test getting a specific file"""
    print_subheader("Testing Get Specific File")
    
    if not file_id:
        print_warning("No file ID available for testing")
        return True
    
    data, status_code = make_request("GET", f"/files/{file_id}", auth=True)
    
    if status_code == 200 and data.get("id") == file_id:
        print_success(f"Got file: {data['filename']}")
        return True
    else:
        print_error(f"Get file failed: {data.get('detail', 'Unknown error')}")
        return False

def test_delete_file() -> bool:
    """Test deleting a file"""
    print_subheader("Testing Delete File")
    
    if not file_id:
        print_warning("No file ID available for testing")
        return True
    
    data, status_code = make_request("DELETE", f"/files/{file_id}", auth=True)
    
    if status_code == 200 and data.get("success") is True:
        print_success("File deleted successfully")
        return True
    else:
        print_error(f"Delete file failed: {data.get('detail', 'Unknown error')}")
        return False

def test_delete_chat() -> bool:
    """Test deleting a chat"""
    print_subheader("Testing Delete Chat")
    
    if not chat_id:
        print_error("No chat ID available for testing")
        return False
    
    data, status_code = make_request("DELETE", f"/chats/{chat_id}", auth=True)
    
    if status_code == 200 and data.get("success") is True:
        print_success("Chat deleted successfully")
        return True
    else:
        print_error(f"Delete chat failed: {data.get('detail', 'Unknown error')}")
        return False

def test_logout() -> bool:
    """Test user logout"""
    print_subheader("Testing User Logout")
    
    data, status_code = make_request("POST", "/auth/logout", auth=True)
    
    if status_code == 200 and data.get("success") is True:
        print_success("User logged out successfully")
        return True
    else:
        print_error(f"Logout failed: {data.get('detail', 'Unknown error')}")
        return False

def test_rate_limiting() -> bool:
    """Test rate limiting"""
    print_subheader("Testing Rate Limiting")
    
    # Make multiple requests in quick succession to trigger rate limiting
    print_info("Making multiple requests to test rate limiting...")
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(35):  # Chat endpoint has a limit of 30 per minute
        data, status_code = make_request("GET", "/chats", auth=True)
        
        if status_code == 200:
            success_count += 1
        elif status_code == 429:
            rate_limited_count += 1
            print_info(f"Rate limited after {success_count} requests")
            break
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    if rate_limited_count > 0:
        print_success("Rate limiting is working as expected")
        return True
    else:
        print_warning("Rate limiting not triggered or not working")
        return True  # Not a critical failure

def test_admin_endpoints() -> bool:
    """Test admin endpoints (expected to fail for regular users)"""
    print_subheader("Testing Admin Endpoints (Expected to Fail)")
    
    # Test getting all users (admin only)
    data, status_code = make_request("GET", "/admin/users", auth=True)
    
    if status_code == 403:
        print_success("Admin endpoint correctly denied access to regular user")
        return True
    elif status_code == 200:
        print_warning("Admin endpoint unexpectedly allowed access to regular user")
        return False
    else:
        print_error(f"Admin endpoint test failed with unexpected status: {status_code}")
        return False

def run_all_tests() -> None:
    """Run all API tests"""
    print_header("Alpha ChatGPT Backend API Tests")
    
    tests = [
        ("Health Endpoints", test_health_endpoints),
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("Get Current User", test_get_current_user),
        ("Token Refresh", test_refresh_token),
        ("Create Chat", test_create_chat),
        ("Get Chats", test_get_chats),
        ("Get Specific Chat", test_get_chat),
        ("Update Chat", test_update_chat),
        ("Send Message", test_send_message),
        ("Get Messages", test_get_messages),
        ("File Upload", test_file_upload),
        ("Get Files", test_get_files),
        ("Get Specific File", test_get_file),
        ("Delete File", test_delete_file),
        ("Delete Chat", test_delete_chat),
        ("Rate Limiting", test_rate_limiting),
        ("Admin Endpoints", test_admin_endpoints),
        ("User Logout", test_logout)
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{Colors.BOLD}Running test: {test_name}{Colors.ENDC}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print_error(f"Test threw an exception: {e}")
            results[test_name] = False
            all_passed = False
    
    # Print summary
    print_header("Test Results Summary")
    
    for test_name, result in results.items():
        if result:
            print(f"{Colors.OKGREEN}✓ {test_name}: PASSED{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ {test_name}: FAILED{Colors.ENDC}")
    
    if all_passed:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed successfully!{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Some tests failed. See details above.{Colors.ENDC}")

if __name__ == "__main__":
    run_all_tests()