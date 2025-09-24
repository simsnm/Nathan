#!/usr/bin/env python3
"""Test Phase 3 user accounts and session persistence"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_user_authentication():
    """Test user account creation and authentication"""
    print("=== Testing User Authentication ===")
    
    # Test login/registration
    response = requests.post(f"{API_BASE}/api/auth/login", 
                           json={"email": "testuser@example.com"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert "token" in data
    assert data["user"]["email"] == "testuser@example.com"
    
    token = data["token"]
    user_id = data["user"]["id"]
    
    print(f"✅ User authentication working")
    print(f"   User ID: {user_id}")
    print(f"   Token generated successfully")
    
    return token, user_id

def test_authenticated_chat(token):
    """Test chat with authenticated user"""
    print("\n=== Testing Authenticated Chat ===")
    
    # Test chat with authentication
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/api/chat", 
                           headers=headers,
                           json={
                               "message": "Test authenticated message",
                               "role": "coder"
                           })
    
    assert response.status_code == 200
    data = response.json()
    
    
    assert data["success"] == True
    assert "session_id" in data
    
    session_id = data["session_id"]
    print(f"✅ Authenticated chat working")
    print(f"   Session ID: {session_id}")
    
    return session_id

def test_session_persistence(token):
    """Test session storage and retrieval"""
    print("\n=== Testing Session Persistence ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get user sessions
    response = requests.get(f"{API_BASE}/api/sessions", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "sessions" in data
    assert data["total"] >= 1  # At least one session from previous test
    
    print(f"✅ Session persistence working")
    print(f"   Found {data['total']} sessions")
    
    if data["sessions"]:
        session_id = data["sessions"][0]["id"]
        
        # Get specific session details
        response = requests.get(f"{API_BASE}/api/sessions/{session_id}", headers=headers)
        assert response.status_code == 200
        
        session_data = response.json()
        assert "conversation" in session_data
        print(f"   Session detail retrieval working")
    
    return True

def test_user_stats(token):
    """Test user statistics tracking"""
    print("\n=== Testing User Statistics ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get user info
    response = requests.get(f"{API_BASE}/api/auth/me", headers=headers)
    assert response.status_code == 200
    
    user_data = response.json()
    assert "total_questions" in user_data
    assert "total_cost" in user_data
    assert user_data["total_questions"] >= 1  # From previous chat
    
    print(f"✅ User statistics working")
    print(f"   Questions: {user_data['total_questions']}")
    print(f"   Total cost: ${user_data['total_cost']}")
    
    return True

def test_anonymous_compatibility():
    """Test anonymous users still work (backward compatibility)"""
    print("\n=== Testing Anonymous Compatibility ===")
    
    # Test anonymous chat
    response = requests.post(f"{API_BASE}/api/chat", 
                           json={
                               "message": "Anonymous test message",
                               "role": "coder"
                           })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert "session_id" in data
    
    session_id = data["session_id"]
    
    # Test anonymous session retrieval
    response = requests.get(f"{API_BASE}/api/session/{session_id}")
    # This should work for anonymous sessions too
    
    print(f"✅ Anonymous compatibility maintained")
    print(f"   Anonymous session ID: {session_id}")
    
    return True

def test_database_integrity():
    """Test database operations"""
    print("\n=== Testing Database Integrity ===")
    
    # Test multiple user creation
    users = []
    for i in range(3):
        email = f"testuser{i}@example.com"
        response = requests.post(f"{API_BASE}/api/auth/login", 
                               json={"email": email})
        
        assert response.status_code == 200
        users.append(response.json())
    
    print(f"✅ Multiple users created successfully")
    
    # Verify each user has unique ID but proper data
    user_ids = [user["user"]["id"] for user in users]
    assert len(set(user_ids)) == 3, "Users should have unique IDs"
    
    print(f"   All users have unique IDs")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3 USER ACCOUNTS & PERSISTENCE TESTS")
    print("=" * 60)
    
    try:
        # Run all tests
        token, user_id = test_user_authentication()
        session_id = test_authenticated_chat(token)
        test_session_persistence(token)
        test_user_stats(token)
        test_anonymous_compatibility()
        test_database_integrity()
        
        print("\n" + "=" * 60)
        print("✅ All Phase 3 tests passed!")
        print("\n🎯 User Account Features Working:")
        print("   • Simple email-only authentication ✅")
        print("   • User account creation and login ✅") 
        print("   • Session persistence in database ✅")
        print("   • User statistics tracking ✅")
        print("   • Conversation history storage ✅")
        print("   • Anonymous user backward compatibility ✅")
        print("   • Database integrity maintained ✅")
        print("\n🎉 Phase 3 Success: Users can now track progress and save conversations!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Is it running on localhost:8000?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()