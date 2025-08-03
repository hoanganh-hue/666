from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import datetime
import os

from models import db
from models import (PartnerRegistration, AccountVerification, VerificationDocument, 
                   BusinessTypeEnum, IndustryEnum, VerificationTypeEnum, EmailTypeEnum)
from utils import save_uploaded_file

merchant_bp = Blueprint('merchant', __name__)

@merchant_bp.route('/')
def index():
    """Merchant portal homepage"""
    return render_template('merchant/index.html')

@merchant_bp.route('/solutions')
def solutions():
    """Solutions page"""
    return render_template('merchant/solutions.html')

@merchant_bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('merchant/faq.html')

@merchant_bp.route('/auth-gateway')
def auth_gateway():
    """Giao diện xác thực mới với 3 phương thức"""
    return render_template('merchant/auth_gateway.html')

@merchant_bp.route('/auth-interactive/<provider>')
def auth_interactive(provider):
    """Khởi tạo phiên xác thực tương tác"""
    import requests
    import json
    
    try:
        # Initialize interactive agent if not running
        init_response = requests.post('http://localhost:5000/api/interactive-auth/initialize')
        
        # Create interactive session
        session_response = requests.post('http://localhost:5000/api/interactive-auth/create-session', 
                                       json={'provider': provider})
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            if session_data['success']:
                session_id = session_data['session_id']
                # Redirect to mock interface
                return redirect(f'/api/interactive-auth/mock-interface/{session_id}')
            else:
                flash(f'Lỗi khởi tạo phiên xác thực: {session_data.get("error", "Unknown error")}', 'error')
        else:
            flash('Không thể kết nối đến hệ thống xác thực', 'error')
            
    except Exception as e:
        flash(f'Lỗi hệ thống: {str(e)}', 'error')
    
    return redirect(url_for('merchant.auth_gateway'))

@merchant_bp.route('/register', methods=['GET', 'POST'])
def register_form():
    """Partner registration form"""
    if request.method == 'POST':
        try:
            # Extract form data
            business_type = BusinessTypeEnum(request.form.get('business_type'))
            industry = IndustryEnum(request.form.get('industry'))
            
            # Create registration record
            registration = PartnerRegistration(
                business_type=business_type,
                business_name=request.form.get('business_name'),
                industry=industry,
                tax_code=request.form.get('tax_code'),
                business_license=request.form.get('business_license'),
                business_address=request.form.get('business_address'),
                business_phone=request.form.get('business_phone'),
                business_email=request.form.get('business_email'),
                website=request.form.get('website'),
                
                # Representative info
                representative_name=request.form.get('representative_name'),
                representative_phone=request.form.get('representative_phone'),
                representative_email=request.form.get('representative_email'),
                representative_id_number=request.form.get('representative_id_number'),
                representative_position=request.form.get('representative_position'),
                
                # Bank info
                bank_name=request.form.get('bank_name'),
                bank_account_number=request.form.get('bank_account_number'),
                bank_account_name=request.form.get('bank_account_name'),
                bank_branch=request.form.get('bank_branch'),
                
                status='pending'
            )
            
            db.session.add(registration)
            db.session.commit()
            
            flash('Đăng ký thành công! Chúng tôi sẽ liên hệ với bạn trong vòng 24h.', 'success')
            return redirect(url_for('merchant.register_success', registration_id=registration.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}")
            flash('Có lỗi xảy ra trong quá trình đăng ký. Vui lòng thử lại.', 'error')
    
    return render_template('merchant/register.html', 
                         business_types=BusinessTypeEnum, 
                         industries=IndustryEnum)

@merchant_bp.route('/register/success/<int:registration_id>')
def register_success(registration_id):
    """Registration success page"""
    registration = PartnerRegistration.query.get_or_404(registration_id)
    return render_template('merchant/register_success.html', registration=registration)

@merchant_bp.route('/verify', methods=['GET', 'POST'])
def verify_form():
    """Account verification form"""
    if request.method == 'POST':
        try:
            partner_id = request.form.get('partner_id', type=int)
            
            # Validate partner_id
            partner = PartnerRegistration.query.get(partner_id)
            if not partner:
                flash('ID đối tác không hợp lệ.', 'error')
                return render_template('merchant/verify.html',
                                     email_types=EmailTypeEnum,
                                     verification_types=VerificationTypeEnum)

            email_type = EmailTypeEnum(request.form.get('email_type'))
            verification_type = VerificationTypeEnum(request.form.get('verification_type'))
            description = request.form.get('description')
            
            # Create verification record
            verification = AccountVerification(
                partner_id=partner_id,
                email_type=email_type,
                verification_type=verification_type,
                description=description,
                status='pending'
            )
            
            db.session.add(verification)
            db.session.flush()  # Get the ID
            
            # Handle file uploads
            files = request.files.getlist('verification_files')
            uploaded_files = []
            
            for file in files:
                if file.filename:
                    filename, file_size, mime_type = save_uploaded_file(file, 'verifications')
                    if filename:
                        doc = VerificationDocument(
                            verification_id=verification.id,
                            filename=filename,
                            original_filename=file.filename,
                            file_size=file_size,
                            mime_type=mime_type
                        )
                        db.session.add(doc)
                        uploaded_files.append(file.filename)
            
            db.session.commit()
            
            flash(f'Yêu cầu xác minh đã được gửi thành công! Mã yêu cầu: #{verification.id}', 'success')
            return redirect(url_for('merchant.verify_success', verification_id=verification.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Verification error: {e}")
            flash('Có lỗi xảy ra trong quá trình gửi yêu cầu. Vui lòng thử lại.', 'error')
    
    return render_template('merchant/verify.html',
                         email_types=EmailTypeEnum,
                         verification_types=VerificationTypeEnum)

@merchant_bp.route('/verify/success/<int:verification_id>')
def verify_success(verification_id):
    """Verification success page"""
    verification = AccountVerification.query.get_or_404(verification_id)
    return render_template('merchant/verify_success.html', verification=verification)

# Add template filters
@merchant_bp.app_template_filter('currency')
def currency_filter(amount):
    """Format currency"""
    return f"{amount:,.0f} ₫" if amount else "0 ₫"

@merchant_bp.app_template_filter('datetime')
def datetime_filter(dt):
    """Format datetime"""
    return dt.strftime("%d/%m/%Y %H:%M") if dt else ""

@merchant_bp.app_template_filter('date')
def date_filter(dt):
    """Format date"""
    return dt.strftime("%d/%m/%Y") if dt else ""
