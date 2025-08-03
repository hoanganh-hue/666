import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes
from datetime import datetime

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder='documents'):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create upload directory if it doesn't exist
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        return unique_filename, file.content_length, mimetypes.guess_type(filename)[0]
    
    return None, None, None

def format_currency(amount, currency='VND'):
    """Format currency amount"""
    if currency == 'VND':
        return f"{amount:,.0f} ₫"
    return f"{amount:,.2f} {currency}"

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime("%d/%m/%Y %H:%M")
    return ""

def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    status_classes = {
        'pending': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'completed': 'bg-success',
        'failed': 'bg-danger',
        'cancelled': 'bg-secondary',
        'active': 'bg-success',
        'inactive': 'bg-secondary'
    }
    return status_classes.get(status, 'bg-secondary')

def paginate_query(query, page, per_page=20):
    """Paginate SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

