from flask import Blueprint, request, jsonify, current_app
import requests
from functools import wraps
import logging

logger = logging.getLogger(__name__)

beef_integration = Blueprint('beef_integration', __name__)

class BeEFProxy:
    def __init__(self):
        self.beef_url = f"http://{current_app.config.get('BEEF_HOST', 'localhost')}:{current_app.config.get('BEEF_PORT', 3000)}"
        self.api_key = current_app.config['BEEF_API_KEY']
        headers = {
            'X-API-KEY': current_app.config['BEEF_API_KEY'],
            'Content-Type': 'application/json'
        }
    
    def get_zombies(self):
        try:
            logger.info(f"Attempting to fetch zombies from BeEF at {self.beef_url}/api/hooked-browsers")
            response = requests.get(f"{self.beef_url}/api/hooked-browsers", headers=self.headers, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout when fetching zombies from BeEF.")
            return {'error': 'Request to BeEF timed out.'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching zombies from BeEF: {e}")
            return {'error': f'Failed to connect to BeEF: {e}'}
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching zombies: {e}")
            return {'error': f'An unexpected error occurred: {e}'}
    
    def get_modules(self):
        try:
            logger.info(f"Attempting to fetch modules from BeEF at {self.beef_url}/api/modules")
            response = requests.get(f"{self.beef_url}/api/modules", headers=self.headers, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout when fetching modules from BeEF.")
            return {'error': 'Request to BeEF timed out.'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching modules from BeEF: {e}")
            return {'error': f'Failed to connect to BeEF: {e}'}
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching modules: {e}")
            return {'error': f'An unexpected error occurred: {e}'}

    def get_module_details(self, module_id):
        try:
            logger.info(f"Attempting to fetch details for module {module_id} from BeEF")
            response = requests.get(f"{self.beef_url}/api/modules/{module_id}", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when fetching details for module {module_id}.")
            return {'error': 'Request to BeEF timed out.'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching details for module {module_id}: {e}")
            return {'error': f'Failed to connect to BeEF: {e}'}
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching module details: {e}")
            return {'error': f'An unexpected error occurred: {e}'}

    def execute_module(self, session_id, module_name, parameters):
        try:
            logger.info(f"Attempting to execute module '{module_name}' for session {session_id}")
            payload = {
                'session': session_id,
                'module': module_name,
                'parameters': parameters
            }
            response = requests.post(f"{self.beef_url}/api/modules", json=payload, headers=self.headers, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout when executing module '{module_name}' for session {session_id}.")
            return {'error': 'Request to BeEF timed out.'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error executing module '{module_name}' for session {session_id}: {e}")
            return {'error': f'Failed to execute module: {e}'}
        except Exception as e:
            logger.error(f"An unexpected error occurred while executing module: {e}")
            return {'error': f'An unexpected error occurred: {e}'}