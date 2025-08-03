#!/usr/bin/env python3
"""
Production server runner cho ZaloPay Portal
Chạy với: python run_prod.py
"""

import os
import sys
import logging
from app import create_app
from models import db

def setup_logging():
    """Thiết lập logging cho production"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_production_server():
    """Chạy production server với Gunicorn"""
    
    # Set environment variables for production
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('FLASK_DEBUG', '0')
    
    # Setup logging
    setup_logging()
    
    # Tạo app instance
    app = create_app('production')
    
    # Tạo database tables nếu chưa có
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created/verified")
        except Exception as e:
            logging.error(f"Database error: {e}")
            sys.exit(1)
    
    logging.info("Starting ZaloPay Portal Production Server...")
    logging.info("Merchant Portal: http://0.0.0.0:5000")
    logging.info("Admin Portal: http://0.0.0.0:5000/admin")
    
    # Chạy với Gunicorn
    import subprocess
    cmd = [
        'gunicorn',
        '--bind', '0.0.0.0:5000',
        '--workers', '4',
        '--worker-class', 'sync',
        '--timeout', '120',
        '--keepalive', '2',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--preload',
        '--access-logfile', 'logs/access.log',
        '--error-logfile', 'logs/error.log',
        '--log-level', 'info',
        'main:app'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Gunicorn failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Production server stopped")

if __name__ == '__main__':
    run_production_server()
