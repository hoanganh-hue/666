from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_user, logout_user, login_required, current_user, login_url
from werkzeug.security import check_password_hash
from urllib.parse import urlparse as url_parse
from datetime import datetime
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

from models import db, AdminUser, ActivityLog

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=4)])
    remember_me = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    logger.debug(f"Login page accessed. Is authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to dashboard.")
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = AdminUser.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data):
                if not user.is_active:
                    flash('Tài khoản đã bị vô hiệu hóa.', 'error')
                    return render_template('admin/login.html', form=form)
                
                # Login successful
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                
                # Log login activity
                activity = ActivityLog(
                    admin_user_id=user.id,
                    action='login',
                    resource_type='AdminUser',
                    resource_id=user.id,
                    details=f'User {user.username} logged in successfully',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(activity)
                db.session.commit()
                
                flash(f'Chào mừng {user.full_name or user.username}!', 'success')
                
                # Handle redirection to the originally requested page
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('admin.dashboard')
                return redirect(next_page)
                
            else:
                # Log failed login attempt
                if user:
                    activity = ActivityLog(
                        admin_user_id=user.id,
                        action='login_failed',
                        resource_type='AdminUser',
                        resource_id=user.id,
                        details=f'Failed login attempt for user {form.username.data}',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    db.session.add(activity)
                    db.session.commit()
                
                flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            db.session.rollback()
            flash('Có lỗi xảy ra trong quá trình đăng nhập. Vui lòng thử lại sau.', 'error')
    
    return render_template('admin/login.html', form=form)

@auth_bp.before_app_request
def before_request():
    """Ensure user is logged in and active for all routes"""
    logger.debug(f"Before request: Path={request.path}, Is authenticated={current_user.is_authenticated}")
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.is_active:
            logger.warning(f"Deactivated user {current_user.username} attempted to access. Logging out.")
            logout_user()
            return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    try:
        # Log logout activity
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action='logout',
            resource_type='AdminUser',
            resource_id=current_user.id,
            details=f'User {current_user.username} logged out',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        logout_user()
        flash('Bạn đã đăng xuất thành công.', 'info')
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        logout_user()
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Admin user profile"""
    return render_template('admin/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change admin password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Mật khẩu hiện tại không đúng'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Mật khẩu mới không khớp'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Mật khẩu mới phải có ít nhất 6 ký tự'}), 400
        
        # Update password
        current_user.set_password(new_password)
        
        # Log password change
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action='change_password',
            resource_type='AdminUser',
            resource_id=current_user.id,
            details=f'User {current_user.username} changed password',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Change password error: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi đổi mật khẩu'}), 500

@auth_bp.route('/api/current-user')
@login_required
def current_user_api():
    """Get current admin user information"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'role': current_user.role,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })
