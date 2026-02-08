"""Test Salla API Connection"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

api_base_url = os.getenv('SALLA_API_BASE_URL')
api_token = os.getenv('SALLA_API_TOKEN')

print("🔍 Testing Salla API Connection\n")
print("=" * 60)
print(f"API Base URL: {api_base_url}")
print(f"API Token: {api_token[:20]}..." if api_token else "API Token: NOT SET")
print("=" * 60)
print()

if not api_token:
    print("❌ ERROR: SALLA_API_TOKEN is not set in .env file")
    print("\n💡 Please add your Salla API token to .env:")
    print("   SALLA_API_TOKEN=Bearer your_token_here")
    sys.exit(1)

# Test different endpoints
endpoints = [
    '/orders',
    '/customers', 
    '/products'
]

headers = {
    'Authorization': api_token if api_token.startswith('Bearer ') else f'Bearer {api_token}',
    'Accept': 'application/json'
}

print("Testing API endpoints...\n")

for endpoint in endpoints:
    url = f"{api_base_url}{endpoint}"
    print(f"🔌 Testing: {endpoint}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS")
            data = response.json()
            if 'data' in data:
                print(f"   Records: {len(data['data'])}")
        elif response.status_code == 401:
            print(f"   ❌ UNAUTHORIZED - Invalid or expired token")
            print(f"   Response: {response.text[:200]}")
        elif response.status_code == 403:
            print(f"   ❌ FORBIDDEN - Token doesn't have permission")
        elif response.status_code == 404:
            print(f"   ❌ NOT FOUND - Endpoint doesn't exist")
        else:
            print(f"   ❌ ERROR")
            print(f"   Response: {response.text[:200]}")
        
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT - API took too long to respond")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ CONNECTION ERROR - Cannot reach API")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    print()

print("=" * 60)
print("\n💡 Troubleshooting:")
print("   1. Get your API token from: https://salla.dev/")
print("   2. Make sure token is valid and not expired")
print("   3. Check if your Salla account has API access enabled")
print("   4. Verify the token format: Bearer your_token_here")
