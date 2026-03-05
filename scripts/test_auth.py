"""Test authentication endpoints."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx


BASE_URL = "http://localhost:8000"


async def test_auth_flow():
    """Test complete authentication flow."""
    print("🧪 Testing Authentication Flow\n")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Register new user
        print("1️⃣ Testing user registration...")
        register_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=register_data
            )
            
            if response.status_code == 201:
                user = response.json()
                print(f"   ✅ User registered: {user['email']}")
                print(f"   User ID: {user['id']}")
            elif response.status_code == 409:
                print(f"   ⚠️  User already exists (expected if running multiple times)")
            else:
                print(f"   ❌ Registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
        
        # Test 2: Login
        print("\n2️⃣ Testing user login...")
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"   ✅ Login successful")
                print(f"   Token: {access_token[:50]}...")
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
        
        # Test 3: Get current user (protected endpoint)
        print("\n3️⃣ Testing protected endpoint (/auth/me)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user = response.json()
                print(f"   ✅ Protected endpoint accessed")
                print(f"   User: {user['full_name']} ({user['email']})")
            else:
                print(f"   ❌ Failed to access protected endpoint: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
        
        # Test 4: Invalid token
        print("\n4️⃣ Testing invalid token...")
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=invalid_headers
            )
            
            if response.status_code == 401:
                print(f"   ✅ Invalid token correctly rejected")
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
        
        # Test 5: Wrong password
        print("\n5️⃣ Testing wrong password...")
        wrong_login = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=wrong_login
            )
            
            if response.status_code == 401:
                print(f"   ✅ Wrong password correctly rejected")
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    print("\n" + "="*50)
    print("✅ All authentication tests passed!")
    print("="*50)
    return True


async def main():
    """Main test function."""
    print("Starting authentication tests...")
    print("Make sure the server is running: poetry run python src/main.py\n")
    
    try:
        success = await test_auth_flow()
        sys.exit(0 if success else 1)
    except httpx.ConnectError:
        print("\n❌ Could not connect to server.")
        print("Please start the server first: poetry run python src/main.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
