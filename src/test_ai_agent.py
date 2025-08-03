#!/usr/bin/env python3
"""
Test script for AI Agent Authentication System
"""

import asyncio
import json
import time
import requests
from ai_agent_enhanced import EnhancedBrowserAgent

async def test_enhanced_agent():
    """Test Enhanced AI Agent functionality"""
    print("🤖 Testing Enhanced AI Agent...")
    
    agent = EnhancedBrowserAgent()
    
    try:
        # Initialize agent
        print("1. Initializing agent...")
        success = await agent.initialize()
        if not success:
            print("❌ Failed to initialize agent")
            return
        print("✅ Agent initialized successfully")
        
        # Test Google auth flow
        print("\n2. Testing Google authentication flow...")
        session_id = await agent.create_session('google')
        print(f"✅ Created session: {session_id}")
        
        # Navigate to Google sign-in (without credentials for demo)
        result = await agent.google_auth_flow(session_id)
        print(f"✅ Google auth flow completed: {result['success']}")
        
        if result['success']:
            print(f"   Initial URL: {result['initial_state']['url']}")
            print(f"   Final URL: {result['final_state']['url']}")
            print(f"   Elements found: {len(result['initial_state'].get('elements', []))}")
        
        # Test screenshot capture
        print("\n3. Testing screenshot capture...")
        screenshot = await agent.capture_screenshot(session_id)
        if screenshot:
            print(f"✅ Screenshot captured: {len(screenshot)} characters")
        else:
            print("❌ Failed to capture screenshot")
        
        # Test page analysis
        print("\n4. Testing page analysis...")
        analysis = await agent.analyze_page_elements(session_id)
        if 'error' not in analysis:
            print(f"✅ Page analysis completed")
            print(f"   URL: {analysis.get('url', 'N/A')}")
            print(f"   Title: {analysis.get('title', 'N/A')}")
            print(f"   Elements: {len(analysis.get('elements', []))}")
            print(f"   Errors: {len(analysis.get('errors', []))}")
        else:
            print(f"❌ Page analysis failed: {analysis['error']}")
        
        # Test form field detection
        print("\n5. Testing form field detection...")
        form_fields = await agent.detect_form_fields(session_id)
        if form_fields:
            print(f"✅ Form fields detected:")
            for field_type, fields in form_fields.items():
                print(f"   {field_type}: {len(fields)} fields")
        
        # Cleanup session
        print("\n6. Cleaning up session...")
        await agent.cleanup_session(session_id)
        print("✅ Session cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Cleanup all
        await agent.cleanup_all()
        print("✅ All resources cleaned up")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test initialize endpoint
    print("1. Testing initialize endpoint...")
    try:
        response = requests.post(f"{base_url}/api/ai-auth/initialize")
        if response.status_code == 200:
            print("✅ Initialize endpoint working")
        else:
            print(f"❌ Initialize failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Initialize request failed: {e}")
    
    # Test status endpoint
    print("2. Testing status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/ai-auth/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working: {data}")
        else:
            print(f"❌ Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status request failed: {e}")

def test_basic_functionality():
    """Test basic functionality without browser"""
    print("\n🔧 Testing basic functionality...")
    
    # Test imports
    try:
        from ai_agent_auth import BrowserAutomationAgent
        print("✅ Basic AI Agent import successful")
    except Exception as e:
        print(f"❌ Basic AI Agent import failed: {e}")
    
    try:
        from ai_agent_enhanced import EnhancedBrowserAgent
        print("✅ Enhanced AI Agent import successful")
    except Exception as e:
        print(f"❌ Enhanced AI Agent import failed: {e}")
    
    # Test Flask blueprints
    try:
        from ai_agent_auth import ai_agent_bp
        from ai_agent_enhanced import ai_agent_enhanced_bp
        print("✅ Flask blueprints import successful")
    except Exception as e:
        print(f"❌ Flask blueprints import failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting AI Agent Tests...")
    print("=" * 50)
    
    # Test basic functionality first
    test_basic_functionality()
    
    # Test enhanced agent
    await test_enhanced_agent()
    
    # Test API endpoints (requires running server)
    # test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎉 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

