#!/usr/bin/env python3
"""
Development server runner cho ZaloPay Portal
Chạy với: python run_dev.py
"""

import os
import sys
from app import create_app
from models import db

def run_development_server():
    """Chạy development server với cấu hình phù hợp"""
    
    # Set environment variables for development
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Tạo app instance
    app = create_app()
    
    # Tạo database tables nếu chưa có
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created/verified")
        except Exception as e:
            print(f"❌ Database error: {e}")
            sys.exit(1)
    
    print("🚀 Starting ZaloPay Portal Development Server...")
    print("📱 Merchant Portal: http://0.0.0.0:5000")
    print("👨‍💼 Admin Portal: http://0.0.0.0:5000/admin")
    print("🔐 Admin Login: admin/admin123")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Chạy development server
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_development_server()
