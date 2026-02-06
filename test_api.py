#!/usr/bin/env python3
"""
Simple API test script to demonstrate the working endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_login():
    """Test login endpoint."""
    print("🔐 Testing login endpoint...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Login successful!")
        print(f"Access Token: {token_data['access_token'][:50]}...")
        return token_data['access_token']
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_protected_endpoint(token):
    """Test protected endpoint with token."""
    print("👤 Testing protected endpoint (/me)...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ User profile retrieved!")
        print(f"Username: {user_data['username']}")
        print(f"Email: {user_data['email']}")
        print(f"Roles: {[role['name'] for role in user_data['roles']]}")
    else:
        print(f"❌ Failed: {response.text}")
    print()

def test_registration():
    """Test user registration."""
    print("📝 Testing user registration...")
    reg_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "testpass123",
        "confirm_password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=reg_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ Registration successful!")
    else:
        print(f"❌ Registration failed: {response.text}")
    print()

def main():
    """Main test function."""
    print("🚀 ML Workflow Platform API Test")
    print("=" * 40)
    
    # Test basic endpoints
    test_health()
    
    # Test authentication
    token = test_login()
    
    if token:
        # Test protected endpoints
        test_protected_endpoint(token)
    
    # Test registration
    test_registration()
    
    print("🎉 API testing completed!")
    print("\n📊 Available endpoints:")
    print("  • Health: GET /health")
    print("  • Login: POST /api/v1/auth/login")
    print("  • Register: POST /api/v1/auth/register")
    print("  • Profile: GET /api/v1/auth/me")
    print("  • API Docs: GET /docs")
    print("\n👥 Test users:")
    print("  • Admin: username=admin, password=admin123")
    print("  • Data Scientist: username=scientist, password=scientist123")

if __name__ == "__main__":
    main()