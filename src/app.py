import os
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, redirect, url_for, render_template, send_from_directory, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf

logging.basicConfig(level=logging.DEBUG)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, static_url_path="/static")
    app.config.update(
        SECRET_KEY=os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production"),
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=os.environ.get("CSRF_SECRET_KEY", "dev-csrf-secret-key"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Initialize CSRFProtect early
    csrf = CSRFProtect(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    @app.after_request
    def set_csrf_cookie(response):
        if current_user.is_authenticated:
            csrf_token = generate_csrf()
            response.set_cookie('X-CSRFToken', csrf_token, secure=app.config['SESSION_COOKIE_SECURE'],
                             httponly=True, samesite='Lax')
        return response
    
    # Cấu hình cache cho file tĩnh
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
        
    @app.route('/static/<path:path>')
    def serve_static(path):
        return send_from_directory('static', path, cache_timeout=3600)
        
    # Thêm version cho file tĩnh để tránh cache
    @app.context_processor
    def override_url_for():
        return {'url_for': dated_url_for}
        
    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path, endpoint, filename)
                if os.path.exists(file_path):
                    values['_'] = int(os.path.getmtime(file_path))
        return url_for(endpoint, **values)

    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///zalopay_portal.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Cấu hình cache
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600  # 1 giờ
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    # Thêm headers cache-control cho tất cả response
    @app.after_request
    def add_header(response):
        if 'Cache-Control' not in response.headers:
            if request.path.startswith('/static/'):
                response.cache_control.public = True
                response.cache_control.max_age = 3600  # 1 giờ
            else:
                response.cache_control.no_store = True
                response.cache_control.no_cache = True
                response.cache_control.must_revalidate = True
                response.cache_control.max_age = 0
        return response
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Cập nhật để trỏ đến auth_bp.login

    @login_manager.user_loader
    def load_user(user_id):
        from models import AdminUser
        user = AdminUser.query.get(int(user_id))
        if user:
            app.logger.debug(f"User loaded: {user.username}")
        else:
            app.logger.debug(f"User with ID {user_id} not found.")
        return user

    # Import blueprints inside app context but before route definitions
    from admin_views import admin_bp
    from merchant_views import merchant_bp
    from auth import auth_bp
    from ai_agent_auth import ai_agent_bp
    from ai_agent_interactive import ai_agent_interactive_bp
    from beef_integration import beef_integration_bp, init_beef_integration, beef_context_processor
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(merchant_bp, url_prefix='/')
    app.register_blueprint(ai_agent_bp)
    app.register_blueprint(ai_agent_interactive_bp)


    # Exempt AI Agent Interactive blueprint from CSRF protection
    csrf.exempt(ai_agent_interactive_bp)
    
    # Initialize BeEF integration
    init_beef_integration(app)
    
    # Add BeEF context processor
    app.context_processor(beef_context_processor)
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create default admin user if not exists
        from models import AdminUser
        admin_user = AdminUser.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = AdminUser(
                username='admin',
                email='admin@zalopay.vn',
                full_name='System Administrator',
                role='super_admin'
            )
            admin_user.set_password('admin123')  # Change this in production
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info("Created default admin user: admin/admin123")
        else:
            app.logger.info("Default admin user already exists.")
        
        # Ensure /admin/ route is handled correctly
        @app.route('/admin/')
        @login_required
        def admin_redirect():
            return redirect(url_for('admin.dashboard'))

    @app.route('/')
    def index():
        return redirect(url_for('merchant.index'))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from models import db
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Template filters
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format currency"""
        if amount is None:
            return "0 ₫"
        return f"{amount:,.0f} ₫"

    @app.template_filter('datetime')
    def datetime_filter(dt):
        """Format datetime"""
        if dt is None:
            return ""
        return dt.strftime("%d/%m/%Y %H:%M")

    @app.template_filter('date')
    def date_filter(dt):
        """Format date"""
        if dt is None:
            return ""
        return dt.strftime("%d/%m/%Y")

    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """Get status badge class"""
        from utils import get_status_badge_class
        return get_status_badge_class(status)

    # Context processors for global template variables/functions
    @app.context_processor
    def inject_global_data():
        from models import PartnerRegistration, AccountVerification
        def get_pending_registrations_count():
            return PartnerRegistration.query.filter_by(status='pending').count()

        def get_pending_verifications_count():
            return AccountVerification.query.filter_by(status='pending').count()

        return dict(
            get_pending_registrations_count=get_pending_registrations_count,
            get_pending_verifications_count=get_pending_verifications_count
        )

    return app

# Create the application instance
app = create_app()


