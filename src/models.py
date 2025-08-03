from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum

# This will be initialized from app.py
db = SQLAlchemy()

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(200))
    role = db.Column(db.String(50), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def ping(self):
        self.last_login = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

class BusinessTypeEnum(enum.Enum):
    INDIVIDUAL = 'individual'
    ENTERPRISE = 'enterprise'

class IndustryEnum(enum.Enum):
    RESTAURANT = 'restaurant'
    RETAIL = 'retail'
    SERVICES = 'services'
    ENTERTAINMENT = 'entertainment'
    ONLINE = 'online'
    CANTEEN = 'canteen'
    PARKING = 'parking'
    OTHER = 'other'

class PartnerRegistration(db.Model):
    __tablename__ = 'partner_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    business_type = db.Column(db.Enum(BusinessTypeEnum), nullable=False)
    business_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.Enum(IndustryEnum), nullable=False)
    tax_code = db.Column(db.String(50))
    business_license = db.Column(db.String(100))
    business_address = db.Column(db.Text, nullable=False)
    business_phone = db.Column(db.String(20), nullable=False)
    business_email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200))
    
    # Representative info
    representative_name = db.Column(db.String(200), nullable=False)
    representative_phone = db.Column(db.String(20), nullable=False)
    representative_email = db.Column(db.String(120), nullable=False)
    representative_id_number = db.Column(db.String(20), nullable=False)
    representative_position = db.Column(db.String(100))
    
    # Bank info
    bank_name = db.Column(db.String(100), nullable=False)
    bank_account_number = db.Column(db.String(50), nullable=False)
    bank_account_name = db.Column(db.String(200), nullable=False)
    bank_branch = db.Column(db.String(200))
    
    # Status
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    reviewed_at = db.Column(db.DateTime)
    
    reviewer = db.relationship('AdminUser', backref='reviewed_registrations')

class VerificationTypeEnum(enum.Enum):
    IDENTITY = 'identity_verification'
    BUSINESS = 'business_verification'
    FINANCIAL = 'financial_verification'
    ADDRESS = 'address_verification'
    DOCUMENT = 'document_verification'
    OTHER = 'other'

class EmailTypeEnum(enum.Enum):
    BUSINESS = 'business'
    PERSONAL = 'personal'

class AccountVerification(db.Model):
    __tablename__ = 'account_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, nullable=False)
    email_type = db.Column(db.Enum(EmailTypeEnum), nullable=False)
    verification_type = db.Column(db.Enum(VerificationTypeEnum), nullable=False)
    description = db.Column(db.Text)
    
    # Status and processing
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'))
    admin_notes = db.Column(db.Text)
    
    processor = db.relationship('AdminUser', backref='processed_verifications')

class VerificationDocument(db.Model):
    __tablename__ = 'verification_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    verification_id = db.Column(db.Integer, db.ForeignKey('account_verifications.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    verification = db.relationship('AccountVerification', backref='documents')

class TransactionStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    partner_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='VND')
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.PENDING)
    payment_method = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Fees and settlement
    fee_amount = db.Column(db.Numeric(10, 2), default=0)
    net_amount = db.Column(db.Numeric(15, 2))
    settlement_date = db.Column(db.DateTime)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin_user = db.relationship('AdminUser', backref='activity_logs')
