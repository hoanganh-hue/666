"""
AI Agent Authentication System
Hệ thống AI Agent làm trung gian xác thực cho Google, Apple, Email
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import base64
import io
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ai_agent_bp = Blueprint('ai_agent_auth', __name__, url_prefix='/api/auth')

class BrowserAutomationAgent:
    """AI Agent for browser automation authentication"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.session_data = {}
        
    def setup_browser(self, headless=True):
        """Setup Chrome browser with options"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("Browser setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False
    
    def capture_screenshot(self) -> str:
        """Capture screenshot and return as base64"""
        try:
            screenshot = self.driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(screenshot))
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return img_str
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return ""
    
    def analyze_page_content(self) -> Dict[str, Any]:
        """Analyze current page content and extract relevant information"""
        try:
            page_info = {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'screenshot': self.capture_screenshot(),
                'elements': [],
                'forms': [],
                'errors': []
            }
            
            # Find input elements
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            for inp in inputs:
                try:
                    element_info = {
                        'type': inp.get_attribute('type'),
                        'name': inp.get_attribute('name'),
                        'id': inp.get_attribute('id'),
                        'placeholder': inp.get_attribute('placeholder'),
                        'visible': inp.is_displayed()
                    }
                    page_info['elements'].append(element_info)
                except:
                    continue
            
            # Find buttons
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                try:
                    element_info = {
                        'type': 'button',
                        'text': btn.text,
                        'id': btn.get_attribute('id'),
                        'class': btn.get_attribute('class'),
                        'visible': btn.is_displayed()
                    }
                    page_info['elements'].append(element_info)
                except:
                    continue
            
            # Check for error messages
            error_selectors = [
                '[role="alert"]',
                '.error',
                '.alert-danger',
                '.text-danger',
                '[data-testid*="error"]'
            ]
            
            for selector in error_selectors:
                try:
                    errors = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for error in errors:
                        if error.is_displayed() and error.text.strip():
                            page_info['errors'].append(error.text.strip())
                except:
                    continue
            
            return page_info
        except Exception as e:
            logger.error(f"Failed to analyze page content: {e}")
            return {'error': str(e)}
    
    def google_auth_flow(self, email: str = None, password: str = None) -> Dict[str, Any]:
        """Simulate Google authentication flow"""
        try:
            logger.info("Starting Google authentication flow")
            
            # Navigate to Google sign-in
            self.driver.get('https://accounts.google.com/signin')
            time.sleep(3)
            
            # Capture initial page
            initial_state = self.analyze_page_content()
            
            if email and password:
                # Fill email
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'identifierId'))
                )
                email_input.send_keys(email)
                
                # Click Next
                next_button = self.driver.find_element(By.ID, 'identifierNext')
                next_button.click()
                time.sleep(3)
                
                # Fill password
                password_input = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, 'password'))
                )
                password_input.send_keys(password)
                
                # Click Sign In
                signin_button = self.driver.find_element(By.ID, 'passwordNext')
                signin_button.click()
                time.sleep(5)
            
            # Capture final state
            final_state = self.analyze_page_content()
            
            return {
                'success': True,
                'initial_state': initial_state,
                'final_state': final_state,
                'current_url': self.driver.current_url
            }
            
        except Exception as e:
            logger.error(f"Google auth flow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_state': self.analyze_page_content()
            }
    
    def apple_auth_flow(self, email: str = None, password: str = None) -> Dict[str, Any]:
        """Simulate Apple ID authentication flow"""
        try:
            logger.info("Starting Apple authentication flow")
            
            # Navigate to Apple ID sign-in
            self.driver.get('https://appleid.apple.com/sign-in')
            time.sleep(3)
            
            # Capture initial page
            initial_state = self.analyze_page_content()
            
            if email and password:
                # Fill email
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'account_name_text_field'))
                )
                email_input.send_keys(email)
                
                # Fill password
                password_input = self.driver.find_element(By.ID, 'password_text_field')
                password_input.send_keys(password)
                
                # Click Sign In
                signin_button = self.driver.find_element(By.ID, 'sign-in')
                signin_button.click()
                time.sleep(5)
            
            # Capture final state
            final_state = self.analyze_page_content()
            
            return {
                'success': True,
                'initial_state': initial_state,
                'final_state': final_state,
                'current_url': self.driver.current_url
            }
            
        except Exception as e:
            logger.error(f"Apple auth flow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_state': self.analyze_page_content()
            }
    
    def email_auth_flow(self, email: str = None, password: str = None) -> Dict[str, Any]:
        """Simulate email authentication flow (Gmail)"""
        try:
            logger.info("Starting Email authentication flow")
            
            # Navigate to Gmail
            self.driver.get('https://mail.google.com')
            time.sleep(3)
            
            # This will redirect to Google sign-in if not logged in
            initial_state = self.analyze_page_content()
            
            # If redirected to sign-in, use Google flow
            if 'accounts.google.com' in self.driver.current_url:
                return self.google_auth_flow(email, password)
            
            # If already logged in, capture the state
            final_state = self.analyze_page_content()
            
            return {
                'success': True,
                'initial_state': initial_state,
                'final_state': final_state,
                'current_url': self.driver.current_url
            }
            
        except Exception as e:
            logger.error(f"Email auth flow failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_state': self.analyze_page_content()
            }
    
    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup browser: {e}")

# Global agent instance
auth_agent = BrowserAutomationAgent()

@ai_agent_bp.route('/google-proxy', methods=['POST'])
def google_auth_proxy():
    """Google authentication proxy endpoint"""
    try:
        data = request.get_json()
        
        # Setup browser if not already done
        if not auth_agent.driver:
            if not auth_agent.setup_browser(headless=True):
                return jsonify({
                    'success': False,
                    'error': 'Failed to setup browser'
                }), 500
        
        # Get credentials from request or use demo mode
        email = data.get('email')
        password = data.get('password')
        
        # Execute Google auth flow
        result = auth_agent.google_auth_flow(email, password)
        
        if result['success']:
            # Store session data
            session_id = f"google_auth_{int(time.time())}"
            auth_agent.session_data[session_id] = result
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'auth_url': f'/api/auth/interface/{session_id}',
                'initial_state': result['initial_state']
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Google auth proxy error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_agent_bp.route('/apple-proxy', methods=['POST'])
def apple_auth_proxy():
    """Apple authentication proxy endpoint"""
    try:
        data = request.get_json()
        
        # Setup browser if not already done
        if not auth_agent.driver:
            if not auth_agent.setup_browser(headless=True):
                return jsonify({
                    'success': False,
                    'error': 'Failed to setup browser'
                }), 500
        
        # Get credentials from request or use demo mode
        email = data.get('email')
        password = data.get('password')
        
        # Execute Apple auth flow
        result = auth_agent.apple_auth_flow(email, password)
        
        if result['success']:
            # Store session data
            session_id = f"apple_auth_{int(time.time())}"
            auth_agent.session_data[session_id] = result
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'auth_url': f'/api/auth/interface/{session_id}',
                'initial_state': result['initial_state']
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Apple auth proxy error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_agent_bp.route('/email-proxy', methods=['POST'])
def email_auth_proxy():
    """Email authentication proxy endpoint"""
    try:
        data = request.get_json()
        
        # Setup browser if not already done
        if not auth_agent.driver:
            if not auth_agent.setup_browser(headless=True):
                return jsonify({
                    'success': False,
                    'error': 'Failed to setup browser'
                }), 500
        
        # Get credentials from request or use demo mode
        email = data.get('email')
        password = data.get('password')
        
        # Execute Email auth flow
        result = auth_agent.email_auth_flow(email, password)
        
        if result['success']:
            # Store session data
            session_id = f"email_auth_{int(time.time())}"
            auth_agent.session_data[session_id] = result
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'auth_url': f'/api/auth/interface/{session_id}',
                'initial_state': result['initial_state']
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Email auth proxy error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_agent_bp.route('/interface/<session_id>')
def auth_interface(session_id):
    """Display authentication interface based on browser state"""
    try:
        if session_id not in auth_agent.session_data:
            return "Session not found", 404
        
        session_data = auth_agent.session_data[session_id]
        
        return render_template('auth/ai_agent_interface.html', 
                             session_data=session_data,
                             session_id=session_id)
        
    except Exception as e:
        logger.error(f"Auth interface error: {e}")
        return f"Error: {str(e)}", 500

@ai_agent_bp.route('/submit/<session_id>', methods=['POST'])
def submit_auth(session_id):
    """Submit authentication data and get result"""
    try:
        if session_id not in auth_agent.session_data:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Determine auth type from session_id
        if 'google' in session_id:
            result = auth_agent.google_auth_flow(email, password)
        elif 'apple' in session_id:
            result = auth_agent.apple_auth_flow(email, password)
        elif 'email' in session_id:
            result = auth_agent.email_auth_flow(email, password)
        else:
            return jsonify({'success': False, 'error': 'Unknown auth type'}), 400
        
        # Update session data
        auth_agent.session_data[session_id].update(result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Submit auth error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_bp.route('/status/<session_id>')
def auth_status(session_id):
    """Get current authentication status"""
    try:
        if session_id not in auth_agent.session_data:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        session_data = auth_agent.session_data[session_id]
        current_state = auth_agent.analyze_page_content()
        
        return jsonify({
            'success': True,
            'session_data': session_data,
            'current_state': current_state
        })
        
    except Exception as e:
        logger.error(f"Auth status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_bp.route('/cleanup')
def cleanup_agent():
    """Cleanup browser resources"""
    try:
        auth_agent.cleanup()
        auth_agent.session_data.clear()
        return jsonify({'success': True, 'message': 'Cleanup completed'})
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

