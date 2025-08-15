from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
import sys
import json
import csv
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
# --- Load Environment Variables ---
# This loads the .env file for local development.
load_dotenv()

# --- Helper Functions ---
def format_currency(amount, currency_symbol="₹"):
    """Safely format currency amounts, handling non-numeric values"""
    if amount is None or amount == '' or str(amount).lower() in ['n/a', 'na', 'none']:
        return 'N/A'
    
    try:
        # Convert to string and remove any currency symbols or spaces
        amount_str = str(amount).replace(currency_symbol, '').replace(',', '').strip()
        
        # Check if it's a valid number
        if amount_str.replace('.', '').isdigit():
            amount_num = float(amount_str)
            return f"{currency_symbol}{int(amount_num):,}"
        else:
            return 'N/A'
    except (ValueError, TypeError):
        return 'N/A'

# --- Initialize Flask App ---
app = Flask(__name__)
# Enable CORS to allow your frontend to communicate with this backend.
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# Configure session cookies for proper sharing across tabs
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)

# --- CSV File Paths ---
CSV_DIR = "data"
STAFF_CSV = os.path.join(CSV_DIR, "staff.csv")
LOAN_APPLICATIONS_CSV = os.path.join(CSV_DIR, "loan_applications.csv")
COMPREHENSIVE_LOANS_CSV = os.path.join(CSV_DIR, "comprehensive_loans.csv")
USERS_CSV = os.path.join(CSV_DIR, "users.csv")
CHAT_LOGS_CSV = os.path.join(CSV_DIR, "chat_logs.csv")

# Create data directory if it doesn't exist
os.makedirs(CSV_DIR, exist_ok=True)

# --- Configuration & Authentication ---
API_KEY = os.getenv("API_KEY")
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT")
IAM_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"

# --- SMTP Email Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)
FROM_NAME = os.getenv("FROM_NAME", "AI Banking Portal")

# Check if email configuration is available
EMAIL_ENABLED = bool(SMTP_USERNAME and SMTP_PASSWORD)
if not EMAIL_ENABLED:
    print("WARNING: SMTP credentials not configured. Email notifications will be logged only.")
    print("Set SMTP_USERNAME and SMTP_PASSWORD in .env file for actual email sending.")

# Check if essential environment variables are set (warn but don't exit for UI testing)
IBM_ENABLED = bool(API_KEY and AGENT_ENDPOINT)
if not IBM_ENABLED:
    print("WARNING: API_KEY and AGENT_ENDPOINT not set. IBM Watson features will be disabled.")
    print("Only UI testing and CSV functionality will work.")

def get_iam_token():
    """
    Retrieves a temporary IAM access token from IBM Cloud using the API Key.
    This token is required to authenticate requests to the Watsonx agent.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={API_KEY}"
    
    try:
        response = requests.post(IAM_ENDPOINT, headers=headers, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting IAM token: {e}")
        return None

# --- CSV Helper Functions ---
def initialize_csv_files():
    """Initialize CSV files with headers if they don't exist"""
    
    # Initialize staff.csv
    if not os.path.exists(STAFF_CSV):
        with open(STAFF_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'username', 'password_hash', 'email', 'role', 'created_at'])
            # Add default admin user
            admin_id = str(uuid.uuid4())
            admin_password_hash = generate_password_hash('admin123')
            writer.writerow([admin_id, 'admin', admin_password_hash, 'singhishant37@gmail.com', 'admin', datetime.now().isoformat()])
    
    # Initialize users.csv
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'name', 'email', 'phone', 'password_hash', 'created_at'])
    
    # Initialize loan_applications.csv (simple form)
    if not os.path.exists(LOAN_APPLICATIONS_CSV):
        with open(LOAN_APPLICATIONS_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'application_id', 'first_name', 'last_name', 'email', 'phone', 
                'loan_type', 'loan_amount', 'annual_income', 'employment_status', 
                'purpose', 'status', 'created_at'
            ])
    
    # Initialize comprehensive_loans.csv (detailed form)
    if not os.path.exists(COMPREHENSIVE_LOANS_CSV):
        with open(COMPREHENSIVE_LOANS_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'application_id', 'user_email', 'full_name', 'date_of_birth', 'gender', 
                'marital_status', 'nationality', 'contact_number', 'employment_type', 
                'employer_name', 'annual_income', 'existing_loans', 'loan_type', 
                'loan_amount', 'loan_tenure', 'loan_purpose', 'preferred_emi', 
                'cibil_score', 'status', 'eligibility_status', 'eligibility_reason',
                'required_documents', 'uploaded_documents', 'admin_notes', 
                'verification_status', 'created_at', 'updated_at'
            ])
    
    # Initialize document_uploads.csv
    documents_csv = os.path.join(CSV_DIR, "document_uploads.csv")
    if not os.path.exists(documents_csv):
        with open(documents_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'id', 'application_id', 'user_email', 'document_type', 
                'file_name', 'file_path', 'upload_status', 'verified', 
                'admin_comments', 'uploaded_at'
            ])
    
    # Initialize user_alerts.csv
    alerts_csv = os.path.join(CSV_DIR, "user_alerts.csv")
    if not os.path.exists(alerts_csv):
        with open(alerts_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'id', 'user_email', 'application_id', 'alert_type', 
                'title', 'message', 'priority', 'read', 'created_at'
            ])
    
    # Initialize chat_logs.csv
    if not os.path.exists(CHAT_LOGS_CSV):
        with open(CHAT_LOGS_CSV, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'user_message', 'bot_response', 'timestamp', 'session_id'])

def verify_staff_credentials(username, password):
    """Verify staff login credentials"""
    try:
        with open(STAFF_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['username'] == username:
                    if check_password_hash(row['password_hash'], password):
                        return {'success': True, 'user': row}
                    else:
                        return {'success': False, 'error': 'Invalid password'}
            return {'success': False, 'error': 'User not found'}
    except FileNotFoundError:
        return {'success': False, 'error': 'Staff database not found'}

def save_loan_application(loan_data):
    """Save loan application to CSV"""
    try:
        application_id = str(uuid.uuid4())[:8].upper()
        
        with open(LOAN_APPLICATIONS_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                application_id,
                loan_data.get('firstName', ''),
                loan_data.get('lastName', ''),
                loan_data.get('email', ''),
                loan_data.get('phone', ''),
                loan_data.get('loanType', ''),
                loan_data.get('loanAmount', ''),
                loan_data.get('annualIncome', ''),
                loan_data.get('employmentStatus', ''),
                loan_data.get('purpose', ''),
                'pending',
                datetime.now().isoformat()
            ])
        
        return {'success': True, 'application_id': application_id}
    except Exception as e:
        print(f"Error saving loan application: {e}")
        return {'success': False, 'error': str(e)}

def save_chat_log(user_message, bot_response, session_id=None):
    """Save chat interaction to CSV"""
    try:
        chat_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        with open(CHAT_LOGS_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                chat_id,
                user_message,
                bot_response,
                datetime.now().isoformat(),
                session_id
            ])
    except Exception as e:
        print(f"Error saving chat log: {e}")

def get_all_loan_applications():
    """Retrieve all loan applications from both old and new CSV files"""
    try:
        applications = []
        
        # Read old format loan applications
        try:
            with open(LOAN_APPLICATIONS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Add source indicator
                    row['source'] = 'basic'
                    applications.append(row)
        except FileNotFoundError:
            pass
        
        # Read comprehensive loan applications (new format)
        try:
            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Add source indicator and normalize field names for compatibility
                    row['source'] = 'comprehensive'
                    # Map comprehensive fields to admin dashboard expected fields
                    if 'full_name' in row and row['full_name']:
                        # Split full name if available
                        name_parts = row['full_name'].split(' ', 1)
                        row['first_name'] = name_parts[0] if len(name_parts) > 0 else ''
                        row['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
                    else:
                        row['first_name'] = row.get('first_name', '')
                        row['last_name'] = row.get('last_name', '')
                    
                    # Map email field
                    row['email'] = row.get('user_email', row.get('email', ''))
                    
                    # Ensure other required fields exist
                    row['phone'] = row.get('contact_number', row.get('phone', ''))
                    
                    applications.append(row)
        except FileNotFoundError:
            pass
        
        # Sort by creation date (newest first)
        applications.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return applications
    except Exception as e:
        print(f"Error reading loan applications: {e}")
        return []

def get_chat_logs(limit=100):
    """Retrieve recent chat logs"""
    try:
        logs = []
        with open(CHAT_LOGS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                logs.append(row)
        return logs[-limit:]  # Return last N logs
    except FileNotFoundError:
        return []

def calculate_analytics(applications):
    """Calculate analytics data for the dashboard"""
    total_applications = len(applications)
    approved_count = 0
    pending_count = 0
    rejected_count = 0
    loan_types = {}
    total_amount = 0
    valid_amounts = 0
    
    for app in applications:
        # Count status
        status = app.get('status', 'pending').lower()
        if status in ['approved', 'eligibility_assessed']:
            approved_count += 1
        elif status == 'rejected':
            rejected_count += 1
        else:
            pending_count += 1
        
        # Count loan types
        loan_type = app.get('loan_type', app.get('loanType', 'Other'))
        if not loan_type or loan_type.strip() == '':
            loan_type = 'Other'
        loan_types[loan_type] = loan_types.get(loan_type, 0) + 1
        
        # Calculate average amount
        amount = app.get('loan_amount', app.get('loanAmount', ''))
        if amount and str(amount).strip() and str(amount).strip() != 'N/A':
            try:
                amount_val = float(str(amount).replace(',', '').replace('$', '').replace('₹', ''))
                total_amount += amount_val
                valid_amounts += 1
            except (ValueError, TypeError):
                pass
    
    # Calculate average amount
    avg_amount = format_currency(total_amount / valid_amounts if valid_amounts > 0 else 0)
    
    return {
        'total_applications': total_applications,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'loan_types': loan_types,
        'avg_amount': avg_amount
    }

def update_application_status(app_id, new_status, admin_notes=''):
    """Update the status of a loan application"""
    updated = False
    
    # Try updating in comprehensive loans CSV
    try:
        rows = []
        with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get('application_id') == app_id:
                    row['eligibility_status'] = new_status
                    row['status'] = 'eligibility_assessed'
                    if admin_notes:
                        row['admin_notes'] = admin_notes
                    row['updated_at'] = datetime.now().isoformat()
                    updated = True
                rows.append(row)
        
        if updated:
            with open(COMPREHENSIVE_LOANS_CSV, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True
    except FileNotFoundError:
        pass
    
    # Try updating in basic loan applications CSV
    try:
        rows = []
        with open(LOAN_APPLICATIONS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get('application_id') == app_id:
                    row['status'] = new_status.lower()
                    if admin_notes:
                        row['admin_notes'] = admin_notes
                    row['updated_at'] = datetime.now().isoformat()
                    updated = True
                rows.append(row)
        
        if updated:
            with open(LOAN_APPLICATIONS_CSV, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True
    except FileNotFoundError:
        pass
    
    return False

def get_application_documents(app_id):
    """Get all documents for a specific application"""
    documents = []
    try:
        DOCUMENT_UPLOADS_CSV = os.path.join(CSV_DIR, "document_uploads.csv")
        with open(DOCUMENT_UPLOADS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get('application_id') == app_id:
                    documents.append(row)
    except FileNotFoundError:
        pass
    return documents

def get_application_history(app_id):
    """Get history for a specific application"""
    history = []
    try:
        HISTORY_CSV = os.path.join(CSV_DIR, "application_history.csv")
        with open(HISTORY_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get('application_id') == app_id:
                    history.append(row)
    except FileNotFoundError:
        pass
    return sorted(history, key=lambda x: x.get('created_at', ''), reverse=True)

def add_application_history(app_id, user_email, action_type, action_by, action_reason=''):
    """Add an entry to application history"""
    try:
        HISTORY_CSV = os.path.join(CSV_DIR, "application_history.csv")
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(HISTORY_CSV):
            with open(HISTORY_CSV, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['draft_id', 'application_id', 'user_email', 'status', 'action_type', 'action_by', 'action_reason', 'created_at', 'updated_at'])
        
        # Add new history entry
        with open(HISTORY_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            timestamp = datetime.now().isoformat()
            draft_id = str(uuid.uuid4())[:8].upper()
            writer.writerow([draft_id, app_id, user_email, 'processed', action_type, action_by, action_reason, timestamp, timestamp])
        
        return True
    except Exception as e:
        print(f"Error adding application history: {e}")
        return False

def format_currency(value):
    """Format currency values properly"""
    try:
        if value is None or value == '' or value == 'N/A':
            return 'N/A'
        # Remove any existing currency symbols and commas
        clean_value = str(value).replace('$', '').replace(',', '').strip()
        if clean_value == '' or clean_value == 'N/A':
            return 'N/A'
        # Convert to float and format
        float_value = float(clean_value)
        return f"${float_value:,.0f}"
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'

def create_objection(app_id, user_email, reason, requested_docs, created_by):
    """Create a new objection for an application"""
    try:
        OBJECTIONS_CSV = os.path.join(CSV_DIR, "objections.csv")
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(OBJECTIONS_CSV):
            with open(OBJECTIONS_CSV, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['objection_id', 'application_id', 'user_email', 'objection_reason', 'requested_documents', 'status', 'created_by', 'created_at', 'resolved_at'])
        
        # Add new objection
        with open(OBJECTIONS_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            objection_id = str(uuid.uuid4())[:8].upper()
            timestamp = datetime.now().isoformat()
            writer.writerow([objection_id, app_id, user_email, reason, requested_docs, 'pending', created_by, timestamp, ''])
        
        # Add to application history
        add_application_history(app_id, user_email, 'OBJECTION RAISED', created_by, reason)
        
        # Update application status to pending
        update_application_status(app_id, 'OBJECTION_RAISED', f'Objection raised: {reason}')
        
        return objection_id
    except Exception as e:
        print(f"Error creating objection: {e}")
        import traceback
        traceback.print_exc()
        return None

def register_user(user_data):
    """Register a new user"""
    try:
        # Check if user already exists
        with open(USERS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['email'] == user_data.get('email'):
                    return {'success': False, 'error': 'Email already registered'}
        
        # Add new user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(user_data.get('password'))
        
        with open(USERS_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                user_id,
                user_data.get('name'),
                user_data.get('email'),
                user_data.get('phone'),
                password_hash,
                datetime.now().isoformat()
            ])
        
        return {'success': True, 'message': 'User registered successfully'}
    except Exception as e:
        print(f"Error registering user: {e}")
        return {'success': False, 'error': str(e)}

def verify_user_credentials(email, password):
    """Verify user login credentials"""
    try:
        with open(USERS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['email'] == email:
                    if check_password_hash(row['password_hash'], password):
                        return {
                            'success': True, 
                            'user': {
                                'id': row['id'],
                                'name': row['name'],
                                'email': row['email'],
                                'phone': row['phone']
                            }
                        }
                    else:
                        return {'success': False, 'error': 'Invalid password'}
            return {'success': False, 'error': 'Email not found'}
    except FileNotFoundError:
        return {'success': False, 'error': 'User database not found'}

def save_comprehensive_loan_application(loan_data):
    """Save comprehensive loan application to CSV with Watson AI eligibility assessment"""
    try:
        application_id = str(uuid.uuid4())[:8].upper()
        print(f"🔄 Processing loan application {application_id} for {loan_data.get('userEmail', 'unknown user')}")
        
        # Get Watson AI eligibility assessment
        eligibility_assessment = assess_loan_eligibility_with_watson(loan_data)
        print(f"✅ Eligibility assessment completed for {application_id}: {eligibility_assessment['status']}")
        
        print(f"💾 Writing application {application_id} to CSV file {COMPREHENSIVE_LOANS_CSV}")
        with open(COMPREHENSIVE_LOANS_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                application_id,
                loan_data.get('userEmail', ''),
                loan_data.get('full-name', ''),
                loan_data.get('date-of-birth', ''),
                loan_data.get('gender', ''),
                loan_data.get('marital-status', ''),
                loan_data.get('nationality', ''),
                loan_data.get('contact-number', ''),
                loan_data.get('employment-type', ''),
                loan_data.get('employer-name', ''),
                loan_data.get('annual-income', ''),
                loan_data.get('existing-loans', ''),
                loan_data.get('loan-type', ''),
                loan_data.get('loan-amount', ''),
                loan_data.get('loan-tenure', ''),
                loan_data.get('loan-purpose', ''),
                loan_data.get('preferred-emi', ''),
                loan_data.get('cibil-score', ''),
                'eligibility_assessed',  # status
                eligibility_assessment['status'],  # eligibility_status
                eligibility_assessment['reason'],  # eligibility_reason
                eligibility_assessment['documents'],  # required_documents
                '',  # uploaded_documents (empty initially)
                eligibility_assessment['recommendations'],  # admin_notes
                'pending',  # verification_status
                datetime.now().isoformat(),  # created_at
                datetime.now().isoformat()   # updated_at
            ])
        
        print(f"✅ Application {application_id} saved successfully to {COMPREHENSIVE_LOANS_CSV}")
        
        # Send eligibility notification email
        user_email = loan_data.get('userEmail', '')
        user_name = loan_data.get('full-name', 'Applicant')
        
        if eligibility_assessment['status'] == 'APPROVED':
            # Create alert for document submission
            create_user_alert(
                user_email, application_id, 'document_required',
                'Documents Required - Loan Application',
                f'Congratulations! Your loan application {application_id} is pre-approved. Please submit the required documents to complete the process.',
                'high'
            )
            
            email_subject = f"🎉 Loan Pre-Approval - Application {application_id}"            
            email_message = f"""Dear {user_name},

Great news! Your loan application has been PRE-APPROVED by our Watson AI assessment system.

Application Details:
• Application ID: {application_id}
• Loan Type: {loan_data.get('loan-type', 'N/A')}
• Loan Amount: {format_currency(loan_data.get('loan-amount', 'N/A'))}
• Assessment Status: APPROVED

Next Steps:
1. Submit the required documents through your dashboard
2. Wait for our team to verify your documents
3. Receive final approval after document verification

Required Documents:
{eligibility_assessment['documents']}

Please log in to your account and upload these documents to proceed with your loan application.

This pre-approval is valid for 30 days from the date of this email.

Best regards,
AI Banking Portal Team"""

            html_content = create_html_email_template(
                title="Loan Pre-Approval Success!",
                content=f"""Your loan application for {format_currency(loan_data.get('loan-amount', 'N/A'))} has been pre-approved by Watson AI.

Application ID: {application_id}
Loan Type: {loan_data.get('loan-type', 'N/A')}

Required Documents:
{eligibility_assessment['documents']}

Please upload the required documents through your dashboard to complete the process.""",
                cta_text="Upload Documents Now",
                cta_link="http://127.0.0.1:5001/",
                alert_type="success"
            )
            
        elif eligibility_assessment['status'] == 'CONDITIONALLY_APPROVED':
            create_user_alert(
                user_email, application_id, 'conditional_approval',
                'Conditional Approval - Additional Requirements',
                f'Your loan application {application_id} is conditionally approved. Please review requirements and submit documents.',
                'medium'
            )
            
            email_subject = f"⚠️ Conditional Approval - Application {application_id}"
            email_message = f"""Dear {user_name},

Your loan application has received CONDITIONAL APPROVAL from our Watson AI assessment system.

Application Details:
• Application ID: {application_id}
• Loan Type: {loan_data.get('loan-type', 'N/A')}
• Loan Amount: {format_currency(loan_data.get('loan-amount', 'N/A'))}
• Assessment Status: CONDITIONALLY APPROVED

Assessment Details:
Reason: {eligibility_assessment['reason']}

Required Documents:
{eligibility_assessment['documents']}

Recommendations:
{eligibility_assessment['recommendations']}

Please submit the required documents and fulfill the conditions mentioned above to proceed with your loan application.

Best regards,
AI Banking Portal Team"""

            html_content = create_html_email_template(
                title="Conditional Loan Approval",
                content=f"""Your loan application requires additional documentation and review.

Application ID: {application_id}
Status: CONDITIONALLY APPROVED

Assessment Reason:
{eligibility_assessment['reason']}

Required Documents:
{eligibility_assessment['documents']}

Recommendations:
{eligibility_assessment['recommendations']}""",
                cta_text="Complete Requirements",
                cta_link="http://127.0.0.1:5001/",
                alert_type="warning"
            )
            
        else:  # REJECTED
            create_user_alert(
                user_email, application_id, 'rejection',
                'Loan Application Not Approved',
                f'Unfortunately, your loan application {application_id} does not meet current eligibility criteria. Please review the reasons and consider reapplying.',
                'high'
            )
            
            email_subject = f"📋 Loan Application Status - Application {application_id}"
            email_message = f"""Dear {user_name},

Thank you for your interest in our loan services. After careful review by our Watson AI system, your loan application does not currently meet our eligibility criteria.

Application Details:
• Application ID: {application_id}
• Loan Type: {loan_data.get('loan-type', 'N/A')}
• Loan Amount: {format_currency(loan_data.get('loan-amount', 'N/A'))}
• Assessment Status: NOT APPROVED

Assessment Details:
Reason: {eligibility_assessment['reason']}

Recommendations for Future Applications:
{eligibility_assessment['recommendations']}

You may reapply after addressing these requirements. Our customer service team is available to help you improve your eligibility.

We appreciate your interest in our services and look forward to serving you in the future.

Best regards,
AI Banking Portal Team"""

            html_content = create_html_email_template(
                title="Loan Application Status Update",
                content=f"""We have carefully reviewed your loan application using Watson AI technology.

Application ID: {application_id}
Status: NOT APPROVED

Assessment Reason:
{eligibility_assessment['reason']}

Improvement Recommendations:
{eligibility_assessment['recommendations']}

You may reapply once you have addressed these requirements.""",
                cta_text="Learn More About Requirements",
                cta_link="http://127.0.0.1:5001/",
                alert_type="danger"
            )
        
        # Send email notification with HTML content
        send_email_notification(user_email, email_subject, email_message, 'application_status', html_content)
        
        return {
            'success': True, 
            'application_id': application_id,
            'eligibility_status': eligibility_assessment['status'],
            'eligibility_reason': eligibility_assessment['reason'],
            'required_documents': eligibility_assessment['documents'],
            'next_step': 'document_upload' if eligibility_assessment['status'] in ['APPROVED', 'CONDITIONALLY_APPROVED'] else 'eligibility_review'
        }
        
    except Exception as e:
        print(f"Error saving comprehensive loan application: {e}")
        return {'success': False, 'error': str(e)}

def get_user_applications(user_email):
    """Get all loan applications for a specific user"""
    try:
        applications = []
        
        # Get simple applications
        try:
            with open(LOAN_APPLICATIONS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['email'] == user_email:
                        applications.append(row)
        except FileNotFoundError:
            pass
        
        # Get comprehensive applications
        try:
            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['user_email'] == user_email:
                        # Convert comprehensive loan format to simple format for consistency
                        applications.append({
                            'application_id': row['application_id'],
                            'loan_type': row['loan_type'],
                            'loan_amount': row['loan_amount'],
                            'status': row['status'],
                            'created_at': row['created_at'],
                            'eligibility_status': row.get('eligibility_status', ''),
                            'eligibility_reason': row.get('eligibility_reason', ''),
                            'required_documents': row.get('required_documents', ''),
                            'admin_notes': row.get('admin_notes', '')
                        })
        except FileNotFoundError:
            pass
        
        return applications
    except Exception as e:
        print(f"Error getting user applications: {e}")
        return []

def get_user_objected_applications(user_email):
    """Get all objected applications (drafts) for a specific user"""
    try:
        drafts = []
        
        # Get objections for this user
        OBJECTIONS_CSV = os.path.join(CSV_DIR, "objections.csv")
        if not os.path.exists(OBJECTIONS_CSV):
            return []
            
        with open(OBJECTIONS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            user_objections = [row for row in reader if row['user_email'] == user_email and row['status'] == 'pending']
        
        # Get application details for each objection
        for objection in user_objections:
            app_id = objection['application_id']
            
            # Get application details from comprehensive loans
            try:
                with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if row['application_id'] == app_id and row['status'] == 'OBJECTION_RAISED':
                            draft = {
                                'application_id': app_id,
                                'objection_id': objection['objection_id'],
                                'loan_type': row['loan_type'],
                                'loan_amount': row['loan_amount'],
                                'objection_reason': objection['objection_reason'],
                                'requested_documents': objection['requested_documents'],
                                'created_at': row['created_at'],
                                'objection_created_at': objection['created_at'],
                                'current_documents': row.get('uploaded_documents', ''),
                                'full_application': row
                            }
                            drafts.append(draft)
                            break
            except FileNotFoundError:
                continue
                
        return drafts
    except Exception as e:
        print(f"Error getting user objected applications: {e}")
        return []

def resubmit_objected_application(application_id, user_email, new_documents=None):
    """Resubmit an objected application with new documents"""
    try:
        # Update application status to pending review
        update_application_status(application_id, 'resubmitted', 'Application resubmitted with new documents')
        
        # Update objection status to resolved
        OBJECTIONS_CSV = os.path.join(CSV_DIR, "objections.csv")
        if os.path.exists(OBJECTIONS_CSV):
            rows = []
            with open(OBJECTIONS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['application_id'] == application_id and row['user_email'] == user_email and row['status'] == 'pending':
                        row['status'] = 'resolved'
                        row['resolved_at'] = datetime.now().isoformat()
                    rows.append(row)
            
            # Write back updated data
            with open(OBJECTIONS_CSV, 'w', newline='', encoding='utf-8') as file:
                if rows:
                    fieldnames = rows[0].keys()
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
        
        # Add to application history
        add_application_history(application_id, user_email, 'RESUBMITTED', user_email, f'Application resubmitted with new documents: {new_documents or "No new documents"}')
        
        return True
    except Exception as e:
        print(f"Error resubmitting application: {e}")
        return False

def assess_loan_eligibility_with_watson(loan_data):
    """Use Watson AI to assess loan eligibility based on comprehensive data"""
    try:
        # Prepare eligibility assessment prompt for Watson AI
        eligibility_prompt = f"""
        As a banking loan officer AI, assess the loan eligibility for the following applicant and provide detailed analysis:

        APPLICANT DETAILS:
        - Full Name: {loan_data.get('full-name', 'N/A')}
        - Age: {calculate_age_from_dob(loan_data.get('date-of-birth', ''))} years
        - Gender: {loan_data.get('gender', 'N/A')}
        - Marital Status: {loan_data.get('marital-status', 'N/A')}
        - Nationality: {loan_data.get('nationality', 'N/A')}
        - Employment Type: {loan_data.get('employment-type', 'N/A')}
        - Employer/Business: {loan_data.get('employer-name', 'N/A')}
        - Annual Income: ₹{loan_data.get('annual-income', 'N/A')}
        - Existing Loans/EMIs: {loan_data.get('existing-loans', 'None')}
        - CIBIL Score: {loan_data.get('cibil-score', 'N/A')}

        LOAN REQUEST:
        - Loan Type: {loan_data.get('loan-type', 'N/A')}
        - Loan Amount: ₹{loan_data.get('loan-amount', 'N/A')}
        - Loan Tenure: {loan_data.get('loan-tenure', 'N/A')} years
        - Purpose: {loan_data.get('loan-purpose', 'N/A')}
        - Preferred EMI: ₹{loan_data.get('preferred-emi', 'N/A')}

        Please provide:
        1. ELIGIBILITY STATUS: APPROVED/CONDITIONALLY_APPROVED/REJECTED
        2. DETAILED REASON: Explain the decision factors
        3. REQUIRED DOCUMENTS: List specific documents needed if eligible
        4. RECOMMENDATIONS: Suggest improvements if rejected or conditions if conditional

        Format your response as:
        ELIGIBILITY: [status]
        REASON: [detailed explanation]
        DOCUMENTS: [comma-separated list]
        RECOMMENDATIONS: [specific advice]
        """

        if IBM_ENABLED:
            # Get Watson AI assessment
            access_token = get_iam_token()
            if access_token:
                agent_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
                
                payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": eligibility_prompt
                        }
                    ]
                }

                try:
                    agent_response = requests.post(AGENT_ENDPOINT, headers=agent_headers, json=payload)
                    agent_response.raise_for_status()
                    response_json = agent_response.json()
                    
                    choices = response_json.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        watson_response = message.get("content", "")
                        
                        # Parse Watson response
                        return parse_watson_eligibility_response(watson_response)
                
                except Exception as e:
                    print(f"Watson AI request failed: {e}")
                    # Fall back to rule-based assessment
                    return rule_based_eligibility_assessment(loan_data)
        
        # Fallback to rule-based assessment when Watson is not available
        return rule_based_eligibility_assessment(loan_data)
        
    except Exception as e:
        print(f"Eligibility assessment error: {e}")
        return rule_based_eligibility_assessment(loan_data)

def calculate_age_from_dob(dob_str):
    """Calculate age from date of birth string"""
    try:
        if not dob_str:
            return "Unknown"
        
        from datetime import datetime
        dob = datetime.strptime(dob_str, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except:
        return "Unknown"

def parse_watson_eligibility_response(watson_response):
    """Parse Watson AI response into structured format"""
    try:
        lines = watson_response.strip().split('\n')
        eligibility_data = {
            'status': 'PENDING_REVIEW',
            'reason': 'Assessment completed',
            'documents': 'Identity Proof, Income Proof, Address Proof',
            'recommendations': 'Standard documentation required'
        }
        
        for line in lines:
            if line.startswith('ELIGIBILITY:'):
                eligibility_data['status'] = line.replace('ELIGIBILITY:', '').strip()
            elif line.startswith('REASON:'):
                eligibility_data['reason'] = line.replace('REASON:', '').strip()
            elif line.startswith('DOCUMENTS:'):
                eligibility_data['documents'] = line.replace('DOCUMENTS:', '').strip()
            elif line.startswith('RECOMMENDATIONS:'):
                eligibility_data['recommendations'] = line.replace('RECOMMENDATIONS:', '').strip()
        
        return eligibility_data
    except Exception as e:
        print(f"Error parsing Watson response: {e}")
        return {
            'status': 'PENDING_REVIEW',
            'reason': 'Automated assessment completed',
            'documents': 'Identity Proof, Income Proof, Address Proof',
            'recommendations': 'Please submit required documents'
        }

def rule_based_eligibility_assessment(loan_data):
    """Rule-based eligibility assessment when Watson AI is not available"""
    try:
        annual_income = float(loan_data.get('annual-income', 0))
        loan_amount = float(loan_data.get('loan-amount', 0))
        cibil_score = int(loan_data.get('cibil-score', 0)) if loan_data.get('cibil-score', '').isdigit() else 0
        age = calculate_age_from_dob(loan_data.get('date-of-birth', ''))
        
        # Basic eligibility rules
        reasons = []
        status = 'APPROVED'
        
        # Age check
        if isinstance(age, int):
            if age < 21:
                reasons.append('Applicant below minimum age of 21 years')
                status = 'REJECTED'
            elif age > 65:
                reasons.append('Applicant above maximum age of 65 years')
                status = 'REJECTED'
        
        # Income check
        if annual_income < 300000:  # Minimum 3 LPA
            reasons.append('Annual income below minimum requirement of ₹3,00,000')
            status = 'REJECTED'
        
        # Loan amount to income ratio
        if annual_income > 0 and (loan_amount / annual_income) > 5:
            reasons.append('Loan amount exceeds 5 times annual income')
            status = 'CONDITIONALLY_APPROVED'
        
        # CIBIL score check
        if cibil_score < 650:
            reasons.append('CIBIL score below 650')
            if cibil_score < 550:
                status = 'REJECTED'
            else:
                status = 'CONDITIONALLY_APPROVED'
        
        # Determine documents based on loan type and employment
        documents = []
        loan_type = loan_data.get('loan-type', '').lower()
        employment_type = loan_data.get('employment-type', '').lower()
        
        # Common documents
        documents.extend(['Aadhaar Card', 'PAN Card', 'Passport Size Photos', 'Bank Statements (6 months)'])
        
        # Employment specific documents
        if 'salaried' in employment_type:
            documents.extend(['Salary Slips (3 months)', 'Employment Certificate', 'Form 16'])
        else:
            documents.extend(['Business Registration', 'ITR (2 years)', 'Profit & Loss Statement', 'Balance Sheet'])
        
        # Loan type specific documents
        if 'home' in loan_type:
            documents.extend(['Property Documents', 'Sale Agreement', 'Approved Building Plan'])
        elif 'car' in loan_type:
            documents.extend(['Vehicle Quotation', 'Insurance Details'])
        elif 'education' in loan_type:
            documents.extend(['Admission Letter', 'Fee Structure', 'Academic Records'])
        
        # Prepare recommendations
        recommendations = []
        if status == 'REJECTED':
            recommendations.append('Improve CIBIL score and reapply after 6 months')
            recommendations.append('Consider applying for a smaller loan amount')
        elif status == 'CONDITIONALLY_APPROVED':
            recommendations.append('Additional verification required')
            recommendations.append('Co-applicant may be required')
        else:
            recommendations.append('Please submit all required documents for final approval')
        
        return {
            'status': status,
            'reason': '; '.join(reasons) if reasons else 'All eligibility criteria met',
            'documents': ', '.join(documents),
            'recommendations': '; '.join(recommendations)
        }
        
    except Exception as e:
        print(f"Rule-based assessment error: {e}")
        return {
            'status': 'PENDING_REVIEW',
            'reason': 'Manual review required due to assessment error',
            'documents': 'Identity Proof, Income Proof, Address Proof',
            'recommendations': 'Please contact bank for manual assessment'
        }

def send_email_notification(to_email, subject, message, notification_type='info', html_content=None):
    """Send email notification using SMTP"""
    try:
        if not EMAIL_ENABLED:
            # Log email content when SMTP is not configured
            print(f"\n{'='*60}")
            print(f"EMAIL NOTIFICATION [{notification_type.upper()}]")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"From: {FROM_NAME} <{FROM_EMAIL}>")
            print(f"Subject: {subject}")
            print(f"{'='*60}")
            print(f"Message:\n{message}")
            if html_content:
                print(f"\nHTML Content:\n{html_content}")
            print(f"{'='*60}\n")
            
            # Save notification to CSV for tracking
            save_notification_log(to_email, subject, message, notification_type)
            return True

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Create plain text part
        text_part = MIMEText(message, 'plain', 'utf-8')
        msg.attach(text_part)

        # Create HTML part if provided
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
        else:
            # Create a basic HTML version from plain text
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                        <h1 style="margin: 0; font-size: 24px;">🏦 {FROM_NAME}</h1>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 10px; border-left: 4px solid #667eea;">
                        <h2 style="color: #495057; margin-top: 0;">{subject}</h2>
                        <div style="white-space: pre-line; font-size: 16px; line-height: 1.8;">
                            {message}
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 10px;">
                        <p style="margin: 0; color: #6c757d; font-size: 14px;">
                            This is an automated message from AI Banking Portal.<br>
                            Please do not reply to this email.
                        </p>
                        <p style="margin: 10px 0 0 0; color: #6c757d; font-size: 12px;">
                            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                        </p>
                    </div>
                </body>
            </html>
            """
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

        # Connect to server and send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            text = msg.as_string()
            server.sendmail(FROM_EMAIL, to_email, text)
            
        print(f"✅ Email sent successfully to {to_email}: {subject}")
        
        # Save notification to CSV for tracking
        save_notification_log(to_email, subject, message, notification_type)
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("Please check your email credentials in the .env file")
        # Fallback to logging
        print(f"\n📧 EMAIL FALLBACK - To: {to_email}, Subject: {subject}")
        save_notification_log(to_email, subject, message, f"{notification_type}_failed")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error occurred: {e}")
        # Fallback to logging
        print(f"\n📧 EMAIL FALLBACK - To: {to_email}, Subject: {subject}")
        save_notification_log(to_email, subject, message, f"{notification_type}_failed")
        return False
        
    except Exception as e:
        print(f"❌ Email notification error: {e}")
        # Fallback to logging
        print(f"\n📧 EMAIL FALLBACK - To: {to_email}, Subject: {subject}")
        save_notification_log(to_email, subject, message, f"{notification_type}_error")
        return False

def create_html_email_template(title, content, cta_text=None, cta_link=None, alert_type="info"):
    """Create HTML email template"""
    alert_colors = {
        "success": {"bg": "#d4edda", "border": "#28a745", "icon": "✅"},
        "warning": {"bg": "#fff3cd", "border": "#ffc107", "icon": "⚠️"},
        "danger": {"bg": "#f8d7da", "border": "#dc3545", "icon": "❌"},
        "info": {"bg": "#cce7ff", "border": "#007bff", "icon": "ℹ️"}
    }
    
    colors = alert_colors.get(alert_type, alert_colors["info"])
    
    html_template = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 600;">🏦 AI Banking Portal</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Powered by Watson AI Technology</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <div style="background: {colors['bg']}; padding: 25px; border-radius: 12px; border-left: 6px solid {colors['border']}; margin-bottom: 30px;">
                        <h2 style="margin: 0 0 15px 0; color: #495057; font-size: 24px; display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 28px;">{colors['icon']}</span>
                            {title}
                        </h2>
                        <div style="font-size: 16px; line-height: 1.8; white-space: pre-line;">
                            {content}
                        </div>
                    </div>
                    
                    {f'''
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{cta_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 16px; box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);">
                            {cta_text}
                        </a>
                    </div>
                    ''' if cta_text and cta_link else ''}
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 25px 30px; text-align: center; border-top: 1px solid #e9ecef;">
                    <p style="margin: 0; color: #6c757d; font-size: 14px;">
                        This is an automated message from <strong>AI Banking Portal</strong><br>
                        Please do not reply to this email.
                    </p>
                    <p style="margin: 15px 0 0 0; color: #adb5bd; font-size: 12px;">
                        Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html_template

def save_notification_log(email, subject, message, notification_type):
    """Save email notification log to CSV"""
    try:
        notifications_csv = os.path.join(CSV_DIR, "notifications.csv")
        
        # Initialize file if doesn't exist
        if not os.path.exists(notifications_csv):
            with open(notifications_csv, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'email', 'subject', 'message', 'type', 'sent_at'])
        
        # Add notification log
        with open(notifications_csv, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                str(uuid.uuid4()),
                email,
                subject,
                message,
                notification_type,
                datetime.now().isoformat()
            ])
    except Exception as e:
        print(f"Error saving notification log: {e}")

def send_objection_notification(user_email, app_id, reason, requested_docs):
    """Send objection notification email to user"""
    try:
        subject = f"📋 Document Resubmission Required - Application {app_id}"
        
        # Create the apply link
        apply_link = "http://127.0.0.1:5001/apply.html"
        
        message = f"""
Dear Applicant,

We have reviewed your loan application {app_id} and require additional documentation to proceed with the approval process.

OBJECTION DETAILS:
{reason}

REQUESTED DOCUMENTS:
{requested_docs if requested_docs else 'Please check the application portal for specific requirements.'}

NEXT STEPS:
1. Click the link below to access the loan application portal
2. Navigate to your draft applications
3. Upload the requested documents
4. Resubmit your application

Access Portal: {apply_link}

Please ensure all documents are clear, legible, and meet our requirements. If you have any questions, please contact our support team.

Thank you for choosing our banking services.

Best regards,
AI Banking Portal Team
        """
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">📋 Document Resubmission Required</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Application {app_id}</p>
            </div>
            
            <div style="padding: 30px;">
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin-bottom: 25px; border-radius: 0 8px 8px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #92400e;">Objection Details:</h3>
                    <p style="margin: 0; color: #78350f; line-height: 1.6;">{reason}</p>
                </div>
                
                <div style="background: #e0f2fe; border-left: 4px solid #0284c7; padding: 20px; margin-bottom: 25px; border-radius: 0 8px 8px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #0c4a6e;">Requested Documents:</h3>
                    <p style="margin: 0; color: #0c4a6e; line-height: 1.6;">{requested_docs if requested_docs else 'Please check the application portal for specific requirements.'}</p>
                </div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{apply_link}" style="display: inline-block; background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        📄 Access Application Portal
                    </a>
                </div>
                
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin-top: 25px;">
                    <h4 style="margin: 0 0 10px 0; color: #374151;">Next Steps:</h4>
                    <ol style="margin: 0; color: #6b7280; line-height: 1.8;">
                        <li>Click the button above to access the portal</li>
                        <li>Navigate to your draft applications</li>
                        <li>Upload the requested documents</li>
                        <li>Resubmit your application</li>
                    </ol>
                </div>
            </div>
            
            <div style="background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px;">
                <p style="margin: 0;">Thank you for choosing our banking services.</p>
                <p style="margin: 5px 0 0 0;">AI Banking Portal Team</p>
            </div>
        </div>
        """
        
        return send_email_notification(user_email, subject, message, 'objection', html_content)
    except Exception as e:
        print(f"Error sending objection notification: {e}")
        return False

def create_user_alert(user_email, application_id, alert_type, title, message, priority='medium'):
    """Create user alert and save to CSV"""
    try:
        alerts_csv = os.path.join(CSV_DIR, "user_alerts.csv")
        
        with open(alerts_csv, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                str(uuid.uuid4()),
                user_email,
                application_id,
                alert_type,
                title,
                message,
                priority,
                'unread',
                datetime.now().isoformat()
            ])
    except Exception as e:
        print(f"Error creating user alert: {e}")

def get_user_alerts(user_email):
    """Get all alerts for a specific user"""
    try:
        alerts = []
        alerts_csv = os.path.join(CSV_DIR, "user_alerts.csv")
        
        if os.path.exists(alerts_csv):
            with open(alerts_csv, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['user_email'] == user_email:
                        alerts.append(row)
        
        # Sort by created_at descending (newest first)
        alerts.sort(key=lambda x: x['created_at'], reverse=True)
        return alerts
    except Exception as e:
        print(f"Error getting user alerts: {e}")
        return []

def save_document_upload(application_id, user_email, document_type, file_name, file_path):
    """Save document upload information to CSV"""
    try:
        documents_csv = os.path.join(CSV_DIR, "document_uploads.csv")
        
        with open(documents_csv, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                str(uuid.uuid4()),
                application_id,
                user_email,
                document_type,
                file_name,
                file_path,
                'uploaded',
                'pending',
                '',
                datetime.now().isoformat()
            ])
        
        return True
    except Exception as e:
        print(f"Error saving document upload: {e}")
        return False

def get_application_documents(application_id):
    """Get all documents for a specific application"""
    try:
        documents = []
        documents_csv = os.path.join(CSV_DIR, "document_uploads.csv")
        
        if os.path.exists(documents_csv):
            with open(documents_csv, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['application_id'] == application_id:
                        documents.append(row)
        
        return documents
    except Exception as e:
        print(f"Error getting application documents: {e}")
        return []

def update_application_status(application_id, new_status, admin_notes='', verification_status=''):
    """Update application status and admin notes"""
    try:
        # Read all records
        rows = []
        with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        # Update specific application
        updated = False
        for row in rows:
            if row['application_id'] == application_id:
                row['status'] = new_status
                row['updated_at'] = datetime.now().isoformat()
                if admin_notes:
                    row['admin_notes'] = admin_notes
                if verification_status:
                    row['verification_status'] = verification_status
                updated = True
                break
        
        if updated:
            # Write back to file
            with open(COMPREHENSIVE_LOANS_CSV, 'w', newline='', encoding='utf-8') as file:
                if rows:
                    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            return True
        
        return False
    except Exception as e:
        print(f"Error updating application status: {e}")
        return False

def update_uploaded_documents(application_id, uploaded_files):
    """Update the uploaded_documents field for an application"""
    try:
        # Read all records
        rows = []
        with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        # Update specific application
        for row in rows:
            if row['application_id'] == application_id:
                row['uploaded_documents'] = ', '.join(uploaded_files)
                row['updated_at'] = datetime.now().isoformat()
                break
        
        # Write back to file
        with open(COMPREHENSIVE_LOANS_CSV, 'w', newline='', encoding='utf-8') as file:
            if rows:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        return True
    except Exception as e:
        print(f"Error updating uploaded documents: {e}")
        return False

def create_admin_alert(application_id, alert_type, title, message):
    """Create alert for admin dashboard"""
    try:
        admin_alerts_csv = os.path.join(CSV_DIR, "admin_alerts.csv")
        
        # Initialize file if doesn't exist
        if not os.path.exists(admin_alerts_csv):
            with open(admin_alerts_csv, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'application_id', 'alert_type', 'title', 'message', 'status', 'created_at'])
        
        with open(admin_alerts_csv, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                str(uuid.uuid4()),
                application_id,
                alert_type,
                title,
                message,
                'unread',
                datetime.now().isoformat()
            ])
    except Exception as e:
        print(f"Error creating admin alert: {e}")

def get_admin_alerts():
    """Get all alerts for admin dashboard"""
    try:
        alerts = []
        admin_alerts_csv = os.path.join(CSV_DIR, "admin_alerts.csv")
        
        if os.path.exists(admin_alerts_csv):
            with open(admin_alerts_csv, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    alerts.append(row)
        
        # Sort by created_at descending (newest first)
        alerts.sort(key=lambda x: x['created_at'], reverse=True)
        return alerts
    except Exception as e:
        print(f"Error getting admin alerts: {e}")
        return []
        admin_alerts_csv = os.path.join(CSV_DIR, "admin_alerts.csv")
        
        if os.path.exists(admin_alerts_csv):
            with open(admin_alerts_csv, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    alerts.append(row)
        
        # Sort by created_at descending (newest first)
        alerts.sort(key=lambda x: x['created_at'], reverse=True)
        return alerts
    except Exception as e:
        print(f"Error getting admin alerts: {e}")
        return []

# --- API Routes ---
# @app.route('/ask', methods=['POST'])
# def ask_agent():
#     """
#     This endpoint receives a user query, authenticates with IBM,
#     forwards the query to the agent, and returns the agent's response.
#     """
#     # 1. Get a fresh IAM token for this request
#     # This ensures the token is always valid. For higher performance, you could
#     # cache the token and refresh it only when it's about to expire.
#     access_token = get_iam_token()
#     if not access_token:
#         return jsonify({"error": "Failed to authenticate with IBM Cloud. Check API Key and server logs."}), 500

#     # 2. Get the user's query from the incoming request
#     try:
#         request_data = request.get_json()
#         user_query = request_data.get("query")

#         if not user_query:
#             return jsonify({"error": "Query field cannot be empty."}), 400
#     except Exception:
#         return jsonify({"error": "Invalid request format. JSON body with 'query' key is expected."}), 400

#     # 3. Prepare and send the request to the IBM Watsonx Agent
#     agent_headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {access_token}"
#     }
    
#     payload = {
#         "input": user_query
#         # Add other parameters like 'conversation_id' if needed by your agent
#         # "conversation_id": "some-session-id"
#     }

#     try:
#         agent_response = requests.post(AGENT_ENDPOINT, headers=agent_headers, json=payload)
#         agent_response.raise_for_status() # Raise an exception for bad status codes

#         response_json = agent_response.json()
#         # The key for the agent's reply might be 'output' or nested deeper.
#         # Check your agent's response format. Example: result['output']['generic'][0]['text']
#         reply = response_json.get("output", "No output received from agent.")
        
#         return jsonify({"response": reply})

#     except requests.exceptions.HTTPError as e:
#         # This catches errors from the agent endpoint (e.g., 400, 404, 500)
#         return jsonify({
#             "error": "Failed to fetch response from IBM Agent.",
#             "status_code": e.response.status_code,
#             "details": e.response.text
#         }), e.response.status_code
#     except Exception as e:
#         # This catches other errors (e.g., network issues, invalid JSON response)
#         return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# # --- Main Execution ---
# if __name__ == "__main__":
#     # The app runs on port 5000 by default.
#     # You can change it with: app.run(debug=True, port=5001)
#     app.run(debug=True)

# --- Translation and Localization Functions ---

def get_translation_dict():
    """Return comprehensive translation dictionary for all supported languages"""
    return {
        'en': {
            'mock_response': "Thank you for your message: '{query}'. This is a demo response as IBM Watson is not configured. I can help you with loan information, account queries, and banking services.",
            'auth_failed': "Failed to authenticate with IBM Cloud. Check API Key and server logs.",
            'empty_query': "Query field cannot be empty.",
            'invalid_request': "Invalid request format. JSON body with 'query' key is expected.",
            'agent_failed': "Failed to fetch response from IBM Agent.",
            'unexpected_error': "An unexpected error occurred.",
            'ai_prompt_prefix': "Please respond in English. User query: ",
            'loan_approved': "Great news! Your loan application has been PRE-APPROVED by our Watson AI assessment system.",
            'loan_conditional': "Your loan application has received CONDITIONAL APPROVAL from our Watson AI assessment system.",
            'loan_rejected': "Thank you for your interest in our loan services. After careful review by our Watson AI system, your loan application does not currently meet our eligibility criteria.",
        },
        'hi': {
            'mock_response': "आपके संदेश के लिए धन्यवाद: '{query}'। यह एक डेमो प्रतिक्रिया है क्योंकि IBM Watson कॉन्फ़िगर नहीं है। मैं लोन की जानकारी, खाता पूछताछ और बैंकिंग सेवाओं में आपकी सहायता कर सकता हूं।",
            'auth_failed': "IBM Cloud के साथ प्रमाणीकरण में विफल। API Key और सर्वर लॉग्स की जांच करें।",
            'empty_query': "क्वेरी फ़ील्ड खाली नहीं हो सकती।",
            'invalid_request': "अमान्य अनुरोध प्रारूप। 'query' key के साथ JSON body अपेक्षित है।",
            'agent_failed': "IBM Agent से प्रतिक्रिया प्राप्त करने में विफल।",
            'unexpected_error': "एक अप्रत्याशित त्रुटि हुई।",
            'ai_prompt_prefix': "कृपया हिंदी में उत्तर दें। उपयोगकर्ता प्रश्न: ",
            'loan_approved': "बहुत बढ़िया! आपका लोन आवेदन हमारे Watson AI मूल्यांकन सिस्टम द्वारा पूर्व-अनुमोदित किया गया है।",
            'loan_conditional': "आपके लोन आवेदन को हमारे Watson AI मूल्यांकन सिस्टम से सशर्त अनुमोदन मिला है।",
            'loan_rejected': "हमारी लोन सेवाओं में आपकी रुचि के लिए धन्यवाद। हमारे Watson AI सिस्टम द्वारा सावधानीपूर्वक समीक्षा के बाद, आपका लोन आवेदन वर्तमान में हमारी पात्रता मानदंडों को पूरा नहीं करता।",
        },
        'ta': {
            'mock_response': "உங்கள் செய்திக்கு நன்றி: '{query}'। IBM Watson கॉन्फ़िगర் இல்லாததால் இது ஒரு டெமோ பதில். நான் கடன் தகவல், கணக்கு விசாரணைகள் மற்றும் வங்கி சேவைகளில் உங்களுக்கு உதவ முடியும்।",
            'auth_failed': "IBM Cloud உடன் அங்கீகாரம் தோல்வியடைந்தது. API Key மற்றும் சர்வர் பதிவுகளைச் சரிபார்க்கவும்।",
            'empty_query': "வினவல் புலம் காலியாக இருக்க முடியாது।",
            'invalid_request': "தவறான கோரிக்கை வடிவம். 'query' key உடன் JSON body எதிர்பார்க்கப்படுகிறது।",
            'agent_failed': "IBM Agent இலிருந்து பதிலைப் பெறுவதில் தோல்வி।",
            'unexpected_error': "எதிர்பாராத பிழை ஏற்பட்டது।",
            'ai_prompt_prefix': "தயவுசெய்து தமிழில் பதிலளிக்கவும். பயனர் கேள்வி: ",
            'loan_approved': "அருமையான செய்தி! உங்கள் கடன் விண்ணப்பம் எங்கள் Watson AI மதிப்பீட்டு அமைப்பால் முன்-அனுமதிக்கப்பட்டுள்ளது।",
            'loan_conditional': "உங்கள் கடன் விண்ணப்பம் எங்கள் Watson AI மதிப்பீட்டு அமைப்பிலிருந்து நிபந்தனை அனுமதி பெற்றுள்ளது।",
            'loan_rejected': "எங்கள் கடன் சேவைகளில் உங்கள் ஆர்வத்திற்கு நன்றி। எங்கள் Watson AI அமைப்பால் கவனமாக மதிப்பாய்வு செய்த பின், உங்கள் கடன் விண்ணப்பம் தற்போது எங்கள் தகுதி அளவுகோல்களை பூர்த்தி செய்யவில்லை।",
        },
        'te': {
            'mock_response': "మీ సందేశానికి ధన్యవాదాలు: '{query}'। IBM Watson కॉन्फ़िगर్ చేయబడనందున ఇది డెమో ప్రతిస్పందన. నేను రుణ సమాచారం, ఖాతా విచారణలు మరియు బ్యాంకింగ్ సేవలలో మీకు సహాయం చేయగలను।",
            'auth_failed': "IBM Cloud తో ప్రమాణీకరణ విఫలమైంది. API Key మరియు సర్వర్ లాగ్‌లను తనిఖీ చేయండి।",
            'empty_query': "ప్రశ్న ఫీల్డ్ ఖాళీగా ఉండకూడదు।",
            'invalid_request': "చెల్లని అభ్యర్థన ఫార్మాట్. 'query' key తో JSON body అంచనా వేయబడింది।",
            'agent_failed': "IBM Agent నుండి ప్రతిస్పందనను పొందడంలో విఫలమైంది।",
            'unexpected_error': "ఊహించని లోపం సంభవించింది।",
            'ai_prompt_prefix': "దయచేసి తెలుగులో సమాధానం ఇవ్వండి. వినియోగదారు ప్రశ్న: ",
            'loan_approved': "గొప్ప వార్త! మీ రుణ దరఖాస్తు మా Watson AI మూల్యాంకన వ్యవస్థ ద్వారా ముందస్తు-ఆమోదించబడింది।",
            'loan_conditional': "మీ రుణ దరఖాస్తు మా Watson AI మూల్యాంకన వ్యవస్థ నుండి షరతులతో కూడిన ఆమోదం పొందింది।",
            'loan_rejected': "మా రుణ సేవలపై మీ ఆసక్తికి ధన్యవాదాలు। మా Watson AI వ్యవస్థ ద్వారా జాగ్రత్తగా సమీక్షించిన తర్వాత, మీ రుణ దరఖాస్తు ప్రస్తుతం మా అర్హత ప్రమాణాలను తీర్చడంలేదు।",
        }
    }

def get_localized_mock_response(user_query, language='en'):
    """Get localized mock response for when IBM Watson is not configured"""
    translations = get_translation_dict()
    template = translations.get(language, translations['en'])['mock_response']
    return template.format(query=user_query)

def get_localized_error_message(error_type, language='en'):
    """Get localized error messages"""
    translations = get_translation_dict()
    return translations.get(language, translations['en']).get(error_type, translations['en'][error_type])

def get_localized_ai_prompt(user_query, language='en'):
    """Create localized prompt for AI to respond in specific language"""
    translations = get_translation_dict()
    prefix = translations.get(language, translations['en'])['ai_prompt_prefix']
    return prefix + user_query

def translate_ai_response(ai_response, target_language='en'):
    """Translate AI response to target language (basic implementation)"""
    if target_language == 'en':
        return ai_response
    
    # For now, return the original response with a language instruction
    # In production, this would use a proper translation service
    translations = get_translation_dict()
    if target_language in translations:
        # Add a note that response is in the target language
        lang_names = {'hi': 'हिंदी', 'ta': 'தமிழ்', 'te': 'తెలుగు'}
        return f"[{lang_names.get(target_language, target_language)} में उत्तर] {ai_response}"
    
    return ai_response


@app.route('/ask', methods=['POST'])
def ask_agent():
    """
    This endpoint receives a user query, authenticates with IBM,
    forwards the query to the agent, and returns the agent's response.
    """
    
    # Get user's language preference
    request_data = request.get_json()
    user_query = request_data.get("query", "")
    user_language = request_data.get("language", "en")  # Default to English
    
    # Handle case where IBM credentials are not configured
    if not IBM_ENABLED:
        # Provide a mock response for testing with language support
        mock_response = get_localized_mock_response(user_query, user_language)
        
        # Save the chat interaction to CSV
        save_chat_log(user_query, mock_response, session.get('session_id'))
        
        return jsonify({"response": mock_response})
    
    # 1. Get a fresh IAM token for this request
    access_token = get_iam_token()
    if not access_token:
        error_response = get_localized_error_message("auth_failed", user_language)
        save_chat_log(user_query, error_response)
        return jsonify({"error": error_response}), 500

    # 2. Validate the user's query
    try:
        if not user_query:
            error_response = get_localized_error_message("empty_query", user_language)
            return jsonify({"error": error_response}), 400
    except Exception:
        error_response = get_localized_error_message("invalid_request", user_language)
        return jsonify({"error": error_response}), 400

    # 3. Prepare and send the request to the IBM Watsonx Agent with language context
    agent_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Add language context to the AI prompt
    localized_prompt = get_localized_ai_prompt(user_query, user_language)
    
    payload = {
        "messages": [
            {
                "role": "user", 
                "content": localized_prompt
            }
        ]
    }

    try:
        agent_response = requests.post(AGENT_ENDPOINT, headers=agent_headers, json=payload)
        agent_response.raise_for_status()

        response_json = agent_response.json()
        
        reply = "Could not parse agent response."
        choices = response_json.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            ai_reply = message.get("content", reply)
            # Translate AI response if needed
            reply = translate_ai_response(ai_reply, user_language)

        # Save the chat interaction to CSV
        save_chat_log(user_query, reply, session.get('session_id'))
        
        return jsonify({"response": reply})

    except requests.exceptions.HTTPError as e:
        error_response = get_localized_error_message("agent_failed", user_language)
        save_chat_log(user_query, error_response)
        return jsonify({
            "error": error_response,
            "status_code": e.response.status_code,
            "details": e.response.text
        }), e.response.status_code
    except Exception as e:
        error_response = get_localized_error_message("unexpected_error", user_language)
        save_chat_log(user_query, error_response)
        return jsonify({"error": error_response}), 500

@app.route('/staff-login', methods=['POST'])
def staff_login():
    """Handle staff login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'})
        
        auth_result = verify_staff_credentials(username, password)
        
        if auth_result['success']:
            session['staff_user'] = auth_result['user']
            session['logged_in'] = True
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'error': auth_result['error']})
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Login error: {str(e)}'})

@app.route('/apply-loan', methods=['POST'])
def apply_loan():
    """Handle loan application submission"""
    try:
        loan_data = request.get_json()
        
        # Basic validation
        required_fields = ['firstName', 'lastName', 'email', 'phone', 'loanType', 'loanAmount', 'annualIncome', 'employmentStatus', 'purpose']
        for field in required_fields:
            if not loan_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'})
        
        result = save_loan_application(loan_data)
        
        if result['success']:
            return jsonify({
                'success': True, 
                'message': 'Application submitted successfully',
                'applicationId': result['application_id']
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Application error: {str(e)}'})

@app.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard to view loan applications with tabs"""
    if not session.get('logged_in'):
        return redirect('/')
    
    # Get all loan applications
    applications = get_all_loan_applications()
    
    # Debug: Print number of applications found
    print(f"Admin Dashboard: Found {len(applications)} applications")
    for app in applications[:3]:  # Print first 3 for debugging
        print(f"Application: {app.get('application_id', 'N/A')} - {app.get('email', app.get('user_email', 'N/A'))}")
    
    # Calculate analytics data
    analytics_data = calculate_analytics(applications)
    
    # Enhanced HTML template for admin dashboard with tabs
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title data-translate="admin-dashboard">Admin Dashboard</title>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="scripts/language.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
            .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .tabs { display: flex; background: white; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .tab { padding: 15px 25px; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.3s; }
            .tab:hover { background: #f1f5f9; }
            .tab.active { border-bottom-color: #2563eb; background: #eff6ff; color: #2563eb; font-weight: 600; }
            .tab-content { display: none; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .tab-content.active { display: block; }
            .section { margin: 20px 0; }
            .section h2 { color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 0; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { border: 1px solid #e2e8f0; padding: 12px; text-align: left; }
            th { background: #f8fafc; font-weight: 600; }
            .status-pending { background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 4px; }
            .status-approved { background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; }
            .status-rejected { background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; }
            .logout-btn { background: #dc2626; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .logout-btn:hover { background: #b91c1c; }
            .source-tag { font-size: 0.8em; padding: 2px 6px; border-radius: 3px; }
            .source-basic { background: #e0f2fe; color: #0277bd; }
            .source-comprehensive { background: #f3e5f5; color: #7b1fa2; }
            .action-btn { padding: 6px 12px; margin: 2px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
            .view-btn { background: #3b82f6; color: white; }
            .view-btn:hover { background: #2563eb; }
            .approve-btn { background: #10b981; color: white; }
            .approve-btn:hover { background: #059669; }
            .reject-btn { background: #ef4444; color: white; }
            .reject-btn:hover { background: #dc2626; }
            .charts-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
            .chart-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
            .stat-number { font-size: 2em; font-weight: bold; color: #2563eb; }
            .stat-label { color: #64748b; margin-top: 5px; }
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
            .modal-content { background: white; margin: 5% auto; padding: 20px; border-radius: 8px; width: 80%; max-width: 600px; max-height: 80vh; overflow-y: auto; }
            .modal-close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
            .modal-close:hover { color: black; }
            
            /* Filter Styles */
            .filter-container { background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
            .filter-container h3 { margin-top: 0; color: #1e293b; }
            .filter-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; align-items: end; }
            .filter-group { display: flex; flex-direction: column; }
            .filter-group label { font-weight: 600; color: #374151; margin-bottom: 5px; font-size: 0.9em; }
            .filter-group select, .filter-group input { padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 14px; }
            .filter-group select:focus, .filter-group input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
            .filter-btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; }
            .clear-btn { background: #6b7280; color: white; margin-right: 8px; }
            .clear-btn:hover { background: #4b5563; }
            .export-btn { background: #059669; color: white; }
            .export-btn:hover { background: #047857; }
            .filter-results { margin-top: 15px; font-weight: 600; color: #374151; padding: 10px; background: white; border-radius: 4px; border: 1px solid #e2e8f0; }
            .row-hidden { display: none !important; }
        </style>
    </head>
    <body>
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 data-translate="admin-dashboard">🏦 Banking Admin Dashboard</h1>
                    <p>Welcome, """ + session['staff_user']['username'] + """</p>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div class="language-selector">
                        <div class="language-dropdown">
                            <button class="language-btn" id="languageBtn" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 12px; border-radius: 4px; cursor: pointer;">
                                <span class="language-flag" id="currentFlag">🇺🇸</span>
                                <span class="language-text" id="currentLang">English</span>
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="language-menu" id="languageMenu" style="position: absolute; top: 100%; right: 0; background: white; border: 1px solid #e2e8f0; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 1000; min-width: 120px; display: none;">
                                <div class="language-option" onclick="changeLanguage('en')" style="padding: 8px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; color: #1f2937;">
                                    <span class="flag">🇺🇸</span>
                                    <span>English</span>
                                </div>
                                <div class="language-option" onclick="changeLanguage('hi')" style="padding: 8px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; color: #1f2937;">
                                    <span class="flag">🇮🇳</span>
                                    <span>हिंदी</span>
                                </div>
                                <div class="language-option" onclick="changeLanguage('ta')" style="padding: 8px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; color: #1f2937;">
                                    <span class="flag">🇮🇳</span>
                                    <span>தமிழ்</span>
                                </div>
                                <div class="language-option" onclick="changeLanguage('te')" style="padding: 8px 12px; cursor: pointer; display: flex; align-items: center; gap: 8px; color: #1f2937;">
                                    <span class="flag">🇮🇳</span>
                                    <span>తెలుగు</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button class="logout-btn" onclick="location.href='/logout'" data-translate="logout">Logout</button>
                </div>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('applications')" data-translate="loan-applications">📋 Loan Applications</div>
            <div class="tab" onclick="showTab('analytics')" data-translate="analytics">📊 Analytics</div>
        </div>
        
        <div id="applications" class="tab-content active">
            <div class="section">
                <h2>📋 Loan Applications (""" + str(len(applications)) + """)</h2>
                
                <!-- Filter Controls -->
                <div class="filter-container">
                    <h3>🔍 Filter Applications</h3>
                    <div class="filter-row">
                        <div class="filter-group">
                            <label for="statusFilter">Status:</label>
                            <select id="statusFilter" onchange="applyFilters()">
                                <option value="">All Statuses</option>
                                <option value="pending">Pending</option>
                                <option value="approved">Approved</option>
                                <option value="eligibility_assessed">Assessed</option>
                                <option value="rejected">Rejected</option>
                                <option value="objection_raised">Objected</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="typeFilter">Loan Type:</label>
                            <select id="typeFilter" onchange="applyFilters()">
                                <option value="">All Types</option>
                                <option value="personal">Personal Loan</option>
                                <option value="home">Home Loan</option>
                                <option value="car">Car Loan</option>
                                <option value="business">Business Loan</option>
                                <option value="education">Education Loan</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="sourceFilter">Source:</label>
                            <select id="sourceFilter" onchange="applyFilters()">
                                <option value="">All Sources</option>
                                <option value="basic">Basic</option>
                                <option value="comprehensive">Comprehensive</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="amountFilter">Amount Range:</label>
                            <select id="amountFilter" onchange="applyFilters()">
                                <option value="">All Amounts</option>
                                <option value="0-50000">$0 - $50,000</option>
                                <option value="50000-100000">$50,000 - $100,000</option>
                                <option value="100000-250000">$100,000 - $250,000</option>
                                <option value="250000-500000">$250,000 - $500,000</option>
                                <option value="500000+">$500,000+</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="dateFilter">Date Range:</label>
                            <select id="dateFilter" onchange="applyFilters()">
                                <option value="">All Dates</option>
                                <option value="today">Today</option>
                                <option value="week">This Week</option>
                                <option value="month">This Month</option>
                                <option value="quarter">This Quarter</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="searchFilter">Search:</label>
                            <input type="text" id="searchFilter" placeholder="Search by ID, name, or email..." onkeyup="applyFilters()">
                        </div>
                        
                        <div class="filter-group">
                            <button class="filter-btn clear-btn" onclick="clearFilters()">Clear All</button>
                            <button class="filter-btn export-btn" onclick="exportFilteredData()">Export Filtered</button>
                        </div>
                    </div>
                    
                    <div class="filter-results">
                        <span id="filterResults">Showing all """ + str(len(applications)) + """ applications</span>
                    </div>
                </div>
                
                <table id="applicationsTable">
                    <thead>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Loan Type</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Type</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for app in applications:
        # Handle different status values
        status = app.get('status', 'pending')
        status_class = 'status-pending'
        if status.lower() in ['approved', 'eligibility_assessed']:
            status_class = 'status-approved'
        elif status.lower() == 'rejected':
            status_class = 'status-rejected'
        
        # Handle different source types
        source = app.get('source', 'unknown')
        source_class = f'source-{source}'
        
        # Get the display name - handle empty or missing names
        name = f"{app.get('first_name', '')} {app.get('last_name', '')}".strip()
        if not name or name == ' ':
            full_name = app.get('full_name', '')
            if full_name and full_name.strip():
                name = full_name.strip()
            else:
                # Extract name from email if no name provided
                email_user = app.get('email', app.get('user_email', '')).split('@')[0]
                name = email_user.replace('.', ' ').title() if email_user else 'N/A'
        
        # Get email
        email = app.get('email', app.get('user_email', 'N/A'))
        
        # Get loan type - handle missing loan type
        loan_type = app.get('loan_type', app.get('loanType', ''))
        if not loan_type or loan_type.strip() == '':
            loan_type = 'Not Specified'
        
        # Format amount - handle missing or empty amounts
        amount = app.get('loan_amount', app.get('loanAmount', ''))
        if amount and str(amount).strip() and str(amount).strip() != 'N/A':
            try:
                amount_val = float(str(amount).replace(',', ''))
                amount = f"${amount_val:,.0f}"
            except (ValueError, TypeError):
                amount = f"${amount}"
        else:
            amount = 'Not Specified'
        
        dashboard_html += f"""
                    <tr>
                        <td>{app.get('application_id', 'N/A')}</td>
                        <td>{name}</td>
                        <td>{email}</td>
                        <td>{loan_type}</td>
                        <td>{amount}</td>
                        <td><span class="{status_class}">{status}</span></td>
                        <td><span class="source-tag {source_class}">{source}</span></td>
                        <td>{app.get('created_at', 'N/A')[:10]}</td>
                        <td>
                            <button class="action-btn view-btn" onclick="viewApplication('{app.get('application_id', 'N/A')}')">View</button>
                            <button class="action-btn approve-btn" onclick="approveApplication('{app.get('application_id', 'N/A')}')">Approve</button>
                            <button class="action-btn reject-btn" onclick="rejectApplication('{app.get('application_id', 'N/A')}')">Reject</button>
                        </td>
                    </tr>
        """
    
    dashboard_html += """
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="analytics" class="tab-content">
        <div class="section">
            <h2>� Analytics Dashboard</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">""" + str(analytics_data['total_applications']) + """</div>
                    <div class="stat-label">Total Applications</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(analytics_data['approved_count']) + """</div>
                    <div class="stat-label">Approved</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(analytics_data['pending_count']) + """</div>
                    <div class="stat-label">Pending</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + analytics_data['avg_amount'] + """</div>
                    <div class="stat-label">Average Loan Amount</div>
                </div>
            </div>
            
            <div class="charts-container">
                <div class="chart-box">
                    <h3>Application Status Distribution</h3>
                    <canvas id="statusChart" width="400" height="300"></canvas>
                </div>
                <div class="chart-box">
                    <h3>Loan Types Distribution</h3>
                    <canvas id="loanTypeChart" width="400" height="300"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Application Details Modal -->
    <div id="applicationModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div id="modalContent">
                <!-- Application details will be loaded here -->
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching functionality
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Initialize charts if analytics tab is shown
            if (tabName === 'analytics') {
                initCharts();
            }
        }
        
        // Initialize charts
        function initCharts() {
            // Status Chart
            const statusCtx = document.getElementById('statusChart').getContext('2d');
            new Chart(statusCtx, {
                type: 'pie',
                data: {
                    labels: ['Approved', 'Pending', 'Rejected'],
                    datasets: [{
                        data: [""" + str(analytics_data['approved_count']) + """, """ + str(analytics_data['pending_count']) + """, """ + str(analytics_data['rejected_count']) + """],
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // Loan Type Chart
            const loanTypeCtx = document.getElementById('loanTypeChart').getContext('2d');
            new Chart(loanTypeCtx, {
                type: 'doughnut',
                data: {
                    labels: """ + str(list(analytics_data['loan_types'].keys())) + """,
                    datasets: [{
                        data: """ + str(list(analytics_data['loan_types'].values())) + """,
                        backgroundColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        // Application actions
        function viewApplication(appId) {
            fetch(`/view-application/${appId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('modalContent').innerHTML = data.html;
                        document.getElementById('applicationModal').style.display = 'block';
                    } else {
                        alert('Error loading application details: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error: ' + error);
                });
        }
        
        function approveApplication(appId) {
            if (confirm('Are you sure you want to approve this application?')) {
                fetch(`/approve-application/${appId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Application approved successfully!');
                            location.reload();
                        } else {
                            alert('Error approving application: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Error: ' + error);
                    });
            }
        }
        
        function rejectApplication(appId) {
            if (confirm('Are you sure you want to reject this application?')) {
                fetch(`/reject-application/${appId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Application rejected successfully!');
                            location.reload();
                        } else {
                            alert('Error rejecting application: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Error: ' + error);
                    });
            }
        }
        
        function closeModal() {
            document.getElementById('applicationModal').style.display = 'none';
        }
        
        // Modal tab switching
        function showModalTab(tabName, element) {
            // Hide all tab contents
            document.querySelectorAll('.modal-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.modal-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            element.classList.add('active');
        }
        
        // View document
        function viewDocument(filePath, extension) {
            const isImage = ['jpg', 'jpeg', 'png', 'gif'].includes(extension.toLowerCase());
            const url = `/view-document/${filePath}`;
            
            if (isImage) {
                // Show image in a new modal
                const imageModal = document.createElement('div');
                imageModal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0,0,0,0.8); z-index: 2000; display: flex; 
                    justify-content: center; align-items: center;
                `;
                imageModal.innerHTML = `
                    <div style="max-width: 90%; max-height: 90%; position: relative;">
                        <img src="${url}" style="max-width: 100%; max-height: 100%; border-radius: 8px;" />
                        <button onclick="this.parentElement.parentElement.remove()" 
                                style="position: absolute; top: 10px; right: 10px; background: white; 
                                       border: none; border-radius: 50%; width: 30px; height: 30px; 
                                       cursor: pointer; font-size: 18px;">×</button>
                    </div>
                `;
                document.body.appendChild(imageModal);
            } else {
                // Open PDF or other documents in new tab
                window.open(url, '_blank');
            }
        }
        
        // Quick approve/reject functions
        function quickApprove(appId) {
            approveApplication(appId);
        }
        
        function quickReject(appId) {
            rejectApplication(appId);
        }
        
        // Show objection form
        function showObjectionForm(appId) {
            const form = document.createElement('div');
            form.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.5); z-index: 2000; display: flex; 
                justify-content: center; align-items: center;
            `;
            form.innerHTML = `
                <div style="background: white; padding: 30px; border-radius: 12px; max-width: 500px; width: 90%;">
                    <h3 style="margin: 0 0 20px 0; color: #dc2626;">Raise Objection</h3>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">Reason for Objection:</label>
                        <textarea id="objectionReason" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"
                                  placeholder="Please provide a detailed reason for the objection..."></textarea>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">Requested Documents (comma-separated):</label>
                        <input type="text" id="requestedDocs" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"
                               placeholder="e.g., Updated Income Certificate, Bank Statements, ID Proof">
                    </div>
                    <div style="text-align: right;">
                        <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                                style="padding: 10px 20px; border: 1px solid #ddd; background: white; border-radius: 4px; margin-right: 10px; cursor: pointer;">Cancel</button>
                        <button onclick="submitObjection('${appId}', this)" 
                                style="padding: 10px 20px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer;">Submit Objection</button>
                    </div>
                </div>
            `;
            document.body.appendChild(form);
        }
        
        // Submit objection
        function submitObjection(appId, button) {
            const reason = document.getElementById('objectionReason').value.trim();
            const requestedDocs = document.getElementById('requestedDocs').value.trim();
            
            if (!reason) {
                alert('Please provide a reason for the objection.');
                return;
            }
            
            button.disabled = true;
            button.textContent = 'Submitting...';
            
            fetch(`/create-objection/${appId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    reason: reason,
                    requested_documents: requestedDocs
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Objection submitted successfully! User will be notified via email.');
                    button.parentElement.parentElement.parentElement.remove();
                    closeModal();
                    location.reload();
                } else {
                    alert('Error submitting objection: ' + data.error);
                    button.disabled = false;
                    button.textContent = 'Submit Objection';
                }
            })
            .catch(error => {
                alert('Error: ' + error);
                button.disabled = false;
                button.textContent = 'Submit Objection';
            });
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('applicationModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Filter functionality
        let originalRows = [];
        
        // Initialize filters when page loads
        document.addEventListener('DOMContentLoaded', function() {
            const table = document.getElementById('applicationsTable');
            const tbody = table.querySelector('tbody');
            originalRows = Array.from(tbody.querySelectorAll('tr'));
        });
        
        function applyFilters() {
            const statusFilter = document.getElementById('statusFilter').value.toLowerCase();
            const typeFilter = document.getElementById('typeFilter').value.toLowerCase();
            const sourceFilter = document.getElementById('sourceFilter').value.toLowerCase();
            const amountFilter = document.getElementById('amountFilter').value;
            const dateFilter = document.getElementById('dateFilter').value;
            const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
            
            let visibleCount = 0;
            
            originalRows.forEach(row => {
                let showRow = true;
                const cells = row.cells;
                
                // Status filter
                if (statusFilter && !cells[5].textContent.toLowerCase().includes(statusFilter)) {
                    showRow = false;
                }
                
                // Loan type filter
                if (typeFilter && !cells[3].textContent.toLowerCase().includes(typeFilter)) {
                    showRow = false;
                }
                
                // Source filter
                if (sourceFilter && !cells[6].textContent.toLowerCase().includes(sourceFilter)) {
                    showRow = false;
                }
                
                // Amount filter
                if (amountFilter && !filterByAmount(cells[4].textContent, amountFilter)) {
                    showRow = false;
                }
                
                // Date filter
                if (dateFilter && !filterByDate(cells[7].textContent, dateFilter)) {
                    showRow = false;
                }
                
                // Search filter (ID, name, and email)
                if (searchFilter) {
                    const id = cells[0].textContent.toLowerCase();
                    const name = cells[1].textContent.toLowerCase();
                    const email = cells[2].textContent.toLowerCase();
                    if (!id.includes(searchFilter) && !name.includes(searchFilter) && !email.includes(searchFilter)) {
                        showRow = false;
                    }
                }
                
                if (showRow) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            // Update results count
            document.getElementById('filterResults').textContent = `Showing ${visibleCount} of ${originalRows.length} applications`;
        }
        
        function filterByAmount(amountText, range) {
            const amount = parseFloat(amountText.replace(/[$,]/g, ''));
            if (isNaN(amount)) return true; // Include if amount cannot be parsed
            
            switch(range) {
                case '0-50000': return amount <= 50000;
                case '50000-100000': return amount > 50000 && amount <= 100000;
                case '100000-250000': return amount > 100000 && amount <= 250000;
                case '250000-500000': return amount > 250000 && amount <= 500000;
                case '500000+': return amount > 500000;
                default: return true;
            }
        }
        
        function filterByDate(dateText, range) {
            const rowDate = new Date(dateText);
            const today = new Date();
            const diffTime = today - rowDate;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            switch(range) {
                case 'today': return diffDays <= 1;
                case 'week': return diffDays <= 7;
                case 'month': return diffDays <= 30;
                case 'quarter': return diffDays <= 90;
                default: return true;
            }
        }
        
        function clearFilters() {
            document.getElementById('statusFilter').value = '';
            document.getElementById('typeFilter').value = '';
            document.getElementById('sourceFilter').value = '';
            document.getElementById('amountFilter').value = '';
            document.getElementById('dateFilter').value = '';
            document.getElementById('searchFilter').value = '';
            
            // Show all rows
            originalRows.forEach(row => {
                row.style.display = '';
            });
            
            // Update results count
            document.getElementById('filterResults').textContent = `Showing all ${originalRows.length} applications`;
        }
        
        function exportFilteredData() {
            const visibleRows = originalRows.filter(row => row.style.display !== 'none');
            
            if (visibleRows.length === 0) {
                alert('No data to export');
                return;
            }
            
            // Create CSV content
            let csv = 'ID,Name,Email,Loan Type,Amount,Status,Source,Date\\n';
            
            visibleRows.forEach(row => {
                const cells = row.cells;
                const rowData = [
                    cells[0].textContent, // ID
                    cells[1].textContent, // Name
                    cells[2].textContent, // Email
                    cells[3].textContent, // Loan Type
                    cells[4].textContent, // Amount
                    cells[5].textContent.trim(), // Status (remove extra spaces)
                    cells[6].textContent.trim(), // Source
                    cells[7].textContent  // Date
                ];
                csv += rowData.map(field => `"${field.replace(/"/g, '""')}"`).join(',') + '\\n';
            });
            
            // Download CSV
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `filtered_applications_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    </script>
    </body>
    </html>
    """
    
    return dashboard_html

@app.route('/logout')
def logout():
    """Handle staff logout"""
    session.clear()
    return redirect('/')

@app.route('/view-application/<app_id>')
def view_application(app_id):
    """View detailed application information with documents"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Get application details from both CSV files
        application = None
        
        # First check comprehensive loans
        try:
            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('application_id') == app_id:
                        application = row
                        break
        except FileNotFoundError:
            pass
        
        # If not found, check basic loan applications
        if not application:
            try:
                with open(LOAN_APPLICATIONS_CSV, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if row.get('application_id') == app_id:
                            application = row
                            break
            except FileNotFoundError:
                pass
        
        if not application:
            return jsonify({'success': False, 'error': 'Application not found'})
        
        # Get uploaded documents for this application
        documents = get_application_documents(app_id)
        
        # Get application history
        history = get_application_history(app_id)
        
        # Generate detailed HTML for modal
        html = f"""
        <div style="max-height: 80vh; overflow-y: auto;">
            <h2>Application Details - {app_id}</h2>
            
            <!-- Tab Navigation -->
            <div style="display: flex; border-bottom: 1px solid #ddd; margin-bottom: 20px;">
                <button class="modal-tab active" onclick="showModalTab('details', this)">Application Details</button>
                <button class="modal-tab" onclick="showModalTab('documents', this)">Documents ({len(documents)})</button>
                <button class="modal-tab" onclick="showModalTab('history', this)">History</button>
            </div>
            
            <!-- Application Details Tab -->
            <div id="details" class="modal-tab-content active">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h3>Personal Information</h3>
                        <p><strong>Name:</strong> {application.get('full_name', 'N/A')}</p>
                        <p><strong>Email:</strong> {application.get('user_email', application.get('email', 'N/A'))}</p>
                        <p><strong>Date of Birth:</strong> {application.get('date_of_birth', 'N/A')}</p>
                        <p><strong>Gender:</strong> {application.get('gender', 'N/A')}</p>
                        <p><strong>Marital Status:</strong> {application.get('marital_status', 'N/A')}</p>
                        <p><strong>Nationality:</strong> {application.get('nationality', 'N/A')}</p>
                        <p><strong>Contact:</strong> {application.get('contact_number', 'N/A')}</p>
                    </div>
                    <div>
                        <h3>Employment Information</h3>
                        <p><strong>Employment Type:</strong> {application.get('employment_type', 'N/A')}</p>
                        <p><strong>Employer:</strong> {application.get('employer_name', 'N/A')}</p>
                        <p><strong>Annual Income:</strong> {format_currency(application.get('annual_income', 'N/A'))}</p>
                        <p><strong>Existing Loans:</strong> {application.get('existing_loans', 'N/A')}</p>
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <h3>Loan Information</h3>
                    <p><strong>Loan Type:</strong> {application.get('loan_type', 'N/A')}</p>
                    <p><strong>Loan Amount:</strong> {format_currency(application.get('loan_amount', 'N/A'))}</p>
                    <p><strong>Loan Tenure:</strong> {application.get('loan_tenure', 'N/A')} years</p>
                    <p><strong>Loan Purpose:</strong> {application.get('loan_purpose', 'N/A')}</p>
                    <p><strong>Preferred EMI:</strong> {format_currency(application.get('preferred_emi', 'N/A'))}</p>
                    <p><strong>CIBIL Score:</strong> {application.get('cibil_score', 'N/A')}</p>
                </div>
                <div style="margin-top: 20px;">
                    <h3>Application Status</h3>
                    <p><strong>Status:</strong> {application.get('status', 'N/A')}</p>
                    <p><strong>Eligibility Status:</strong> {application.get('eligibility_status', 'N/A')}</p>
                    <p><strong>Eligibility Reason:</strong> {application.get('eligibility_reason', 'N/A')}</p>
                    <p><strong>Required Documents:</strong> {application.get('required_documents', 'N/A')}</p>
                    <p><strong>Uploaded Documents:</strong> {application.get('uploaded_documents', 'N/A')}</p>
                    <p><strong>Created At:</strong> {application.get('created_at', 'N/A')}</p>
                    <p><strong>Updated At:</strong> {application.get('updated_at', 'N/A')}</p>
                </div>
            </div>
            
            <!-- Documents Tab -->
            <div id="documents" class="modal-tab-content">
                <h3>Uploaded Documents</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;">"""
        
        for doc in documents:
            file_extension = doc.get('file_name', '').split('.')[-1].lower()
            is_image = file_extension in ['jpg', 'jpeg', 'png', 'gif']
            
            html += f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: #f9f9f9;">
                        <h4>{doc.get('document_type', 'Unknown')}</h4>
                        <p><strong>File:</strong> {doc.get('file_name', 'N/A')}</p>
                        <p><strong>Status:</strong> <span style="color: {'green' if doc.get('verified') == 'approved' else 'orange' if doc.get('verified') == 'pending' else 'red'}">{doc.get('verified', 'pending').title()}</span></p>
                        <p><strong>Uploaded:</strong> {doc.get('uploaded_at', 'N/A')[:16].replace('T', ' ')}</p>
                        <div style="margin-top: 10px;">
                            <button class="action-btn view-btn" onclick="viewDocument('{doc.get('file_path', '')}', '{file_extension}')">View Document</button>
                        </div>
                    </div>"""
        
        if not documents:
            html += """
                    <p style="text-align: center; color: #666; font-style: italic;">No documents uploaded yet.</p>"""
        
        html += """
                </div>
            </div>
            
            <!-- History Tab -->
            <div id="history" class="modal-tab-content">
                <h3>Application History</h3>
                <div style="border-left: 3px solid #2563eb; margin-left: 10px;">"""
        
        for hist in history:
            status_color = '#10b981' if hist.get('action_type') == 'APPROVED' else '#ef4444' if hist.get('action_type') == 'REJECTED' else '#f59e0b'
            html += f"""
                    <div style="margin-left: 20px; margin-bottom: 20px; position: relative;">
                        <div style="position: absolute; left: -30px; width: 20px; height: 20px; border-radius: 50%; background: {status_color}; border: 3px solid white;"></div>
                        <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="margin: 0; color: {status_color};">{hist.get('action_type', 'N/A')}</h4>
                            <p style="margin: 5px 0; color: #666;"><strong>By:</strong> {hist.get('action_by', 'N/A')}</p>
                            <p style="margin: 5px 0;">{hist.get('action_reason', 'No reason provided')}</p>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #888;">{hist.get('created_at', 'N/A')[:16].replace('T', ' ')}</p>
                        </div>
                    </div>"""
        
        if not history:
            html += """
                    <p style="text-align: center; color: #666; font-style: italic; margin-left: 20px;">No history available.</p>"""
        
        html += """
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center;">"""
        
        html += f"""
                <button class="action-btn approve-btn" onclick="quickApprove('{app_id}')">Quick Approve</button>
                <button class="action-btn reject-btn" onclick="quickReject('{app_id}')">Quick Reject</button>
                <button class="action-btn" style="background: #f59e0b;" onclick="showObjectionForm('{app_id}')">Raise Objection</button>
            </div>
        </div>"""
        
        return jsonify({'success': True, 'html': html})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/approve-application/<app_id>', methods=['POST'])
def approve_application(app_id):
    """Approve a loan application"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        updated = update_application_status(app_id, 'APPROVED', 'Application approved by admin')
        if updated:
            # Add to history
            add_application_history(app_id, '', 'APPROVED', session['staff_user']['username'], 'Application approved by admin')
            return jsonify({'success': True, 'message': 'Application approved successfully'})
        else:
            return jsonify({'success': False, 'error': 'Application not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reject-application/<app_id>', methods=['POST'])
def reject_application(app_id):
    """Reject a loan application"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        updated = update_application_status(app_id, 'REJECTED', 'Application rejected by admin')
        if updated:
            # Add to history
            add_application_history(app_id, '', 'REJECTED', session['staff_user']['username'], 'Application rejected by admin')
            return jsonify({'success': True, 'message': 'Application rejected successfully'})
        else:
            return jsonify({'success': False, 'error': 'Application not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/create-objection/<app_id>', methods=['POST'])
def create_objection_endpoint(app_id):
    """Create objection for an application"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        data = request.json
        reason = data.get('reason', '')
        requested_docs = data.get('requested_documents', '')
        
        if not reason:
            return jsonify({'success': False, 'error': 'Reason is required'})
        
        # Get application details for email
        application = None
        try:
            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('application_id') == app_id:
                        application = row
                        break
        except FileNotFoundError:
            pass
        
        if not application:
            return jsonify({'success': False, 'error': 'Application not found'})
        
        user_email = application.get('user_email', application.get('email', ''))
        objection_id = create_objection(app_id, user_email, reason, requested_docs, session['staff_user']['username'])
        
        if objection_id:
            # Send notification email to user
            send_objection_notification(user_email, app_id, reason, requested_docs)
            return jsonify({'success': True, 'message': 'Objection created successfully', 'objection_id': objection_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to create objection'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/view-document/<path:file_path>')
def view_document(file_path):
    """View a document file"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Security check - ensure file is in uploads directory
        if not file_path.startswith('data/uploads/'):
            return jsonify({'success': False, 'error': 'Invalid file path'})
        
        full_path = os.path.join('/Users/raghavdharwal/data_science_AI/IBMskillbuild/IBM_Bank_Agent/backend', file_path)
        
        if os.path.exists(full_path):
            return send_from_directory(
                os.path.dirname(full_path),
                os.path.basename(full_path)
            )
        else:
            return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-user-drafts', methods=['GET'])
def get_user_drafts():
    """Get draft applications for logged-in user"""
    if not session.get('user_logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        user_email = session.get('user_email')
        drafts = []
        
        # Get objections for this user
        try:
            OBJECTIONS_CSV = os.path.join(CSV_DIR, "objections.csv")
            with open(OBJECTIONS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('user_email') == user_email and row.get('status') == 'pending':
                        # Get application details
                        app_details = None
                        try:
                            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as app_file:
                                app_reader = csv.DictReader(app_file)
                                for app_row in app_reader:
                                    if app_row.get('application_id') == row.get('application_id'):
                                        app_details = app_row
                                        break
                        except FileNotFoundError:
                            pass
                        
                        if app_details:
                            draft = {
                                'objection_id': row.get('objection_id'),
                                'application_id': row.get('application_id'),
                                'loan_type': app_details.get('loan_type', 'N/A'),
                                'loan_amount': app_details.get('loan_amount', 'N/A'),
                                'objection_reason': row.get('objection_reason'),
                                'requested_documents': row.get('requested_documents'),
                                'created_at': row.get('created_at'),
                                'status': 'Pending at Applicant'
                            }
                            drafts.append(draft)
        except FileNotFoundError:
            pass
        
        return jsonify({'success': True, 'drafts': drafts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/user-register', methods=['POST'])
def user_register():
    """User registration endpoint"""
    try:
        data = request.json
        result = register_user(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/user-login', methods=['POST'])
def user_login():
    """User login endpoint"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        result = verify_user_credentials(email, password)
        if result['success']:
            session.permanent = True  # Make session persistent across tabs
            session['user_logged_in'] = True
            session['user_email'] = email
            session['user_data'] = result['user']
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/user-logout', methods=['POST'])
def user_logout():
    """User logout endpoint"""
    session.pop('user_logged_in', None)
    session.pop('user_email', None)
    session.pop('user_data', None)
    return jsonify({'success': True})

@app.route('/user-auth-status', methods=['GET'])
def user_auth_status():
    """Check user authentication status and automatically clear staff sessions"""
    try:
        # Automatically clear any staff sessions when checking user auth
        staff_keys = ['logged_in', 'staff_user', 'username', 'role', 'admin_logged_in']
        for key in staff_keys:
            session.pop(key, None)
        
        if session.get('user_logged_in'):
            # Refresh session to extend timeout
            session.permanent = True
            
            return jsonify({
                'logged_in': True, 
                'email': session.get('user_email'),
                'session_valid': True
            })
        else:
            return jsonify({
                'logged_in': False,
                'session_valid': False
            })
    except Exception as e:
        print(f"Error checking auth status: {e}")
        return jsonify({
            'logged_in': False,
            'session_valid': False,
            'error': str(e)
        })

@app.route('/clear-staff-session', methods=['POST'])
def clear_staff_session():
    """Clear staff session when user interface is accessed"""
    try:
        # Clear all staff-related session keys more thoroughly
        staff_keys = ['logged_in', 'staff_user', 'username', 'role', 'admin_logged_in']
        for key in staff_keys:
            session.pop(key, None)
        
        # Force session regeneration to prevent conflicts
        session.permanent = False
        
        return jsonify({'success': True, 'message': 'Staff session cleared completely'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin-logout', methods=['POST'])
def admin_logout():
    """Force admin logout - more aggressive clearing"""
    try:
        # Clear all session data
        session.clear()
        return jsonify({'success': True, 'message': 'Admin logged out completely'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear-user-session', methods=['POST'])
def clear_user_session():
    """Clear user session when staff logs in"""
    session.pop('user_logged_in', None)
    session.pop('user_email', None)
    session.pop('user_data', None)
    return jsonify({'success': True})

@app.route('/clear-all-sessions', methods=['POST'])
def clear_all_sessions():
    """Clear all sessions (used when returning to main chat)"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'All sessions cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/debug-session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session state (for troubleshooting)"""
    try:
        session_data = {
            'user_logged_in': session.get('user_logged_in', False),
            'user_email': session.get('user_email', None),
            'staff_logged_in': session.get('logged_in', False),
            'session_keys': list(session.keys()),
            'session_permanent': session.permanent
        }
        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/user-applications', methods=['GET'])
def get_user_applications_endpoint():
    """Get all applications for logged-in user"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        user_email = session.get('user_email')
        applications = get_user_applications(user_email)
        return jsonify({'success': True, 'applications': applications})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/user-drafts', methods=['GET'])
def get_user_drafts_endpoint():
    """Get all objected applications (drafts) for logged-in user"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        user_email = session.get('user_email')
        drafts = get_user_objected_applications(user_email)
        return jsonify({'success': True, 'drafts': drafts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/resubmit-application', methods=['POST'])
def resubmit_application_endpoint():
    """Resubmit an objected application"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        data = request.get_json()
        application_id = data.get('application_id')
        user_email = session.get('user_email')
        
        if not application_id:
            return jsonify({'success': False, 'error': 'Application ID is required'})
        
        # Verify this application belongs to the user and is objected
        drafts = get_user_objected_applications(user_email)
        app_exists = any(draft['application_id'] == application_id for draft in drafts)
        
        if not app_exists:
            return jsonify({'success': False, 'error': 'Application not found or not accessible'})
        
        # Get the latest uploaded documents for this application
        uploaded_docs = ""
        try:
            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['application_id'] == application_id:
                        uploaded_docs = row.get('uploaded_documents', '')
                        break
        except FileNotFoundError:
            pass
        
        success = resubmit_objected_application(application_id, user_email, uploaded_docs)
        
        if success:
            return jsonify({'success': True, 'message': 'Application resubmitted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to resubmit application'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_localized_message(key, language='en'):
    """Get localized message for various scenarios"""
    messages = {
        'en': {
            'eligibility_success': 'Congratulations! You are eligible for loan schemes. Please review the recommended options below.',
            'eligibility_failed': 'Based on our assessment, you currently do not meet the eligibility criteria. Please review the improvement suggestions below.',
            'improve_cibil': 'Improve your CIBIL score to 650+ by paying EMIs on time and reducing credit utilization.',
            'improve_income': 'Consider increasing your annual income to ₹3,00,000+ for better loan eligibility.',
            'reduce_loan_amount': 'Consider reducing your loan amount to improve your debt-to-income ratio.',
            'general_improvement': 'Work on improving your financial profile and credit history for better loan eligibility.'
        },
        'hi': {
            'eligibility_success': 'बधाई हो! आप लोन योजनाओं के लिए पात्र हैं। कृपया नीचे दिए गए सुझावों की समीक्षा करें।',
            'eligibility_failed': 'हमारे आकलन के आधार पर, आप वर्तमान में पात्रता मानदंडों को पूरा नहीं करते। कृपया नीचे दिए गए सुधार सुझावों की समीक्षा करें।',
            'improve_cibil': 'समय पर EMI भुगतान करके और क्रेडिट उपयोग कम करके अपना CIBIL स्कोर 650+ तक सुधारें।',
            'improve_income': 'बेहतर लोन पात्रता के लिए अपनी वार्षिक आय ₹3,00,000+ तक बढ़ाने पर विचार करें।',
            'reduce_loan_amount': 'अपने ऋण-से-आय अनुपात में सुधार के लिए लोन राशि कम करने पर विचार करें।',
            'general_improvement': 'बेहतर लोन पात्रता के लिए अपनी वित्तीय प्रोफ़ाइल और क्रेडिट इतिहास में सुधार पर काम करें।'
        },
        'ta': {
            'eligibility_success': 'வாழ்த்துக்கள்! நீங்கள் கடன் திட்டங்களுக்கு தகுதியானவர். கீழே உள்ள பரிந்துரைகளை மதிப்பாய்வு செய்யவும்.',
            'eligibility_failed': 'எங்கள் மதிப்பீட்டின் அடிப்படையில், நீங்கள் தற்போது தகுதி அளவுகோல்களை பூர்த்தி செய்யவில்லை. கீழே உள்ள மேம்பாட்டு பரிந்துரைகளை மதிப்பாய்வு செய்யவும்.',
            'improve_cibil': 'சரியான நேரத்தில் EMI செலுத்துவதன் மூலமும் கடன் பயன்பாட்டை குறைப்பதன் மூலமும் உங்கள் CIBIL ஸ்கோரை 650+ ஆக மேம்படுத்துங்கள்.',
            'improve_income': 'சிறந்த கடன் தகுதிக்காக உங்கள் ஆண்டு வருமானத்தை ₹3,00,000+ ஆக அதிகரிக்க கருதுங்கள்.',
            'reduce_loan_amount': 'உங்கள் கடன்-வருமான விகிதத்தை மேம்படுத்த கடன் தொகையை குறைக்க கருதுங்கள்.',
            'general_improvement': 'சிறந்த கடன் தகுதிக்காக உங்கள் நிதி சுயவிவரம் மற்றும் கடன் வரலாற்றை மேம்படுத்துவதில் கவனம் செலுத்துங்கள்.'
        },
        'te': {
            'eligibility_success': 'అభినందనలు! మీరు లోన్ పథకాలకు అర్హులు. దయచేసి క్రింద ఉన్న సిఫార్సులను సమీక్షించండి.',
            'eligibility_failed': 'మా అంచనా ఆధారంగా, మీరు ప్రస్తుతం అర్హత ప్రమాణాలను తీర్చలేదు. దయచేసి క్రింద ఉన్న మెరుగుదల సూచనలను సమీక్షించండి.',
            'improve_cibil': 'సమయానికి EMI చెల్లించడం మరియు క్రెడిట్ వినియోగాన్ని తగ్గించడం ద్వారా మీ CIBIL స్కోర్‌ను 650+ కి మెరుగుపరచండి.',
            'improve_income': 'మెరుగైన లోన్ అర్హత కోసం మీ వార్షిక ఆదాయాన్ని ₹3,00,000+ కి పెంచడాన్ని పరిగణించండి.',
            'reduce_loan_amount': 'మీ రుణ-ఆదాయ నిష్పత్తిని మెరుగుపరచడానికి లోన్ మొత్తాన్ని తగ్గించడాన్ని పరిగణించండి.',
            'general_improvement': 'మెరుగైన లోన్ అర్హత కోసం మీ ఆర్థిక ప్రొఫైల్ మరియు క్రెడిట్ చరిత్రను మెరుగుపరచడంపై దృష్టి పెట్టండి.'
        }
    }
    
    return messages.get(language, messages['en']).get(key, messages['en'].get(key, ''))

def get_localized_ai_prompt(prompt_type, language, data):
    """Get localized AI prompts for different scenarios"""
    prompts = {
        'en': {
            'loan_assessment': f"""
You are a professional loan officer. Analyze this loan application and provide a comprehensive assessment:

Application Details:
- Name: {data.get('full-name', 'N/A')}
- Age: {data.get('age', 'N/A')}
- Employment: {data.get('employment-type', 'N/A')}
- Annual Income: ₹{data.get('annual-income', 'N/A')}
- Loan Type: {data.get('loan-type', 'N/A')}
- Loan Amount: ₹{data.get('loan-amount', 'N/A')}
- CIBIL Score: {data.get('cibil-score', 'N/A')}
- Existing Loans: {data.get('existing-loans', 'N/A')}

Provide a detailed assessment covering:
1. Strengths of the application
2. Areas of concern (if any)
3. Risk assessment
4. Recommendations

Be professional, constructive, and helpful in your response.
""",
            'scheme_explanation': f"""
You are a banking expert. Explain this loan scheme in detail to help customers understand:

Scheme: {data.get('name', 'N/A')}
Type: {data.get('type', 'N/A')}
Interest Rate: {data.get('interest_rate', 'N/A')}
Tenure: Up to {data.get('max_tenure', 'N/A')} years
Amount Range: ₹{data.get('min_amount', 'N/A')} - ₹{data.get('max_amount', 'N/A')}

Please explain:
1. Who is this scheme best suited for
2. Key benefits and features
3. Important terms and conditions
4. Tips for successful application

Be clear, informative, and customer-friendly.
"""
        },
        'hi': {
            'loan_assessment': f"""
आप एक पेशेवर लोन अधिकारी हैं। इस लोन आवेदन का विश्लेषण करें और एक व्यापक मूल्यांकन प्रदान करें:

आवेदन विवरण:
- नाम: {data.get('full-name', 'N/A')}
- आयु: {data.get('age', 'N/A')}
- रोजगार: {data.get('employment-type', 'N/A')}
- वार्षिक आय: ₹{data.get('annual-income', 'N/A')}
- लोन प्रकार: {data.get('loan-type', 'N/A')}
- लोन राशि: ₹{data.get('loan-amount', 'N/A')}
- CIBIL स्कोर: {data.get('cibil-score', 'N/A')}
- मौजूदा लोन: {data.get('existing-loans', 'N/A')}

निम्नलिखित कवर करते हुए विस्तृत मूल्यांकन प्रदान करें:
1. आवेदन की शक्तियां
2. चिंता के क्षेत्र (यदि कोई हो)
3. जोखिम मूल्यांकन
4. सिफारिशें

अपनी प्रतिक्रिया में पेशेवर, रचनात्मक और सहायक बनें।
""",
            'scheme_explanation': f"""
आप एक बैंकिंग विशेषज्ञ हैं। ग्राहकों को समझने में मदद करने के लिए इस लोन योजना को विस्तार से समझाएं:

योजना: {data.get('name', 'N/A')}
प्रकार: {data.get('type', 'N/A')}
ब्याज दर: {data.get('interest_rate', 'N/A')}
अवधि: {data.get('max_tenure', 'N/A')} वर्ष तक
राशि सीमा: ₹{data.get('min_amount', 'N/A')} - ₹{data.get('max_amount', 'N/A')}

कृपया समझाएं:
1. यह योजना किसके लिए सबसे उपयुक्त है
2. मुख्य लाभ और विशेषताएं
3. महत्वपूर्ण नियम और शर्तें
4. सफल आवेदन के लिए सुझाव

स्पष्ट, जानकारीपूर्ण और ग्राहक-मित्र बनें।
"""
        }
    }
    
    lang_prompts = prompts.get(language, prompts['en'])
    return lang_prompts.get(prompt_type, prompts['en'].get(prompt_type, ''))

# --- Loan Schemes Database ---
LOAN_SCHEMES = {
    "home_loan_standard": {
        "name": "Standard Home Loan",
        "type": "Home Loan",
        "min_amount": 500000,
        "max_amount": 50000000,
        "min_income": 300000,
        "max_tenure": 30,
        "interest_rate": "8.5% - 10.5%",
        "eligibility": {
            "min_age": 21,
            "max_age": 65,
            "employment": ["Salaried", "Self-employed"],
            "cibil_score": 650
        },
        "documents": [
            "Aadhaar Card",
            "PAN Card", 
            "Salary Slips (3 months)",
            "Bank Statements (6 months)",
            "Property Documents",
            "Sale Agreement"
        ],
        "features": [
            "No prepayment charges after 1 year",
            "Flexible repayment options",
            "Property insurance included",
            "Tax benefits under Section 80C & 24"
        ]
    },
    "home_loan_premium": {
        "name": "Premium Home Loan",
        "type": "Home Loan",
        "min_amount": 2000000,
        "max_amount": 100000000,
        "min_income": 1000000,
        "max_tenure": 30,
        "interest_rate": "7.5% - 9.0%",
        "eligibility": {
            "min_age": 25,
            "max_age": 60,
            "employment": ["Salaried", "Self-employed"],
            "cibil_score": 750
        },
        "documents": [
            "Aadhaar Card",
            "PAN Card",
            "Salary Slips (6 months)",
            "Bank Statements (12 months)",
            "Property Documents",
            "Income Tax Returns (2 years)",
            "Property Valuation Report"
        ],
        "features": [
            "Lower interest rates",
            "Higher loan amounts",
            "Dedicated relationship manager",
            "Fast processing in 7 days",
            "No processing fees"
        ]
    },
    "personal_loan_standard": {
        "name": "Standard Personal Loan",
        "type": "Personal Loan",
        "min_amount": 50000,
        "max_amount": 2000000,
        "min_income": 200000,
        "max_tenure": 5,
        "interest_rate": "10.5% - 18.0%",
        "eligibility": {
            "min_age": 21,
            "max_age": 60,
            "employment": ["Salaried", "Self-employed"],
            "cibil_score": 650
        },
        "documents": [
            "Aadhaar Card",
            "PAN Card",
            "Salary Slips (3 months)",
            "Bank Statements (3 months)"
        ],
        "features": [
            "No collateral required",
            "Quick approval in 24 hours",
            "Flexible tenure options",
            "Minimal documentation"
        ]
    },
    "car_loan_standard": {
        "name": "Standard Car Loan",
        "type": "Car Loan",
        "min_amount": 100000,
        "max_amount": 5000000,
        "min_income": 250000,
        "max_tenure": 7,
        "interest_rate": "8.0% - 12.0%",
        "eligibility": {
            "min_age": 21,
            "max_age": 65,
            "employment": ["Salaried", "Self-employed"],
            "cibil_score": 650
        },
        "documents": [
            "Aadhaar Card",
            "PAN Card",
            "Salary Slips (3 months)",
            "Bank Statements (6 months)",
            "Car Quotation",
            "Driving License"
        ],
        "features": [
            "Up to 90% financing",
            "Comprehensive insurance included",
            "Part payment facility",
            "Extended warranty options"
        ]
    },
    "business_loan_sme": {
        "name": "SME Business Loan",
        "type": "Business Loan",
        "min_amount": 500000,
        "max_amount": 10000000,
        "min_income": 500000,
        "max_tenure": 10,
        "interest_rate": "9.5% - 15.0%",
        "eligibility": {
            "min_age": 25,
            "max_age": 65,
            "employment": ["Self-employed", "Business Owner"],
            "cibil_score": 700,
            "business_vintage": 2
        },
        "documents": [
            "Aadhaar Card",
            "PAN Card",
            "Business Registration",
            "GST Returns (12 months)",
            "Bank Statements (12 months)",
            "ITR (2 years)",
            "Financial Statements"
        ],
        "features": [
            "Working capital support",
            "Equipment financing available",
            "Flexible repayment schedules",
            "Business advisory services"
        ]
    },
    "education_loan_standard": {
        "name": "Standard Education Loan",
        "type": "Educational Loan",
        "min_amount": 100000,
        "max_amount": 7500000,
        "min_income": 200000,
        "max_tenure": 15,
        "interest_rate": "8.5% - 11.5%",
        "eligibility": {
            "min_age": 18,
            "max_age": 35,
            "employment": ["Student", "Parent/Guardian"],
            "cibil_score": 650
        },
        "documents": [
            "Aadhaar Card",
            "PAN Card",
            "Admission Letter",
            "Fee Structure",
            "Academic Records",
            "Parent/Guardian Income Proof",
            "Bank Statements (6 months)"
        ],
        "features": [
            "Moratorium period available",
            "Tax benefits under Section 80E",
            "Covers tuition and living expenses",
            "Study abroad options available"
        ]
    }
}

def get_recommended_schemes(application_data):
    """Get loan schemes based on application data"""
    try:
        loan_type = application_data.get('loan-type', '').lower()
        loan_amount = float(application_data.get('loan-amount', 0))
        annual_income = float(application_data.get('annual-income', 0))
        employment_type = application_data.get('employment-type', '')
        cibil_score = int(application_data.get('cibil-score', 600))
        
        # Calculate age from date of birth
        from datetime import datetime
        try:
            dob = datetime.strptime(application_data.get('date-of-birth', ''), '%Y-%m-%d')
            age = (datetime.now() - dob).days // 365
        except:
            age = 30  # Default age
        
        recommended_schemes = []
        
        for scheme_id, scheme in LOAN_SCHEMES.items():
            # Check if scheme matches loan type
            if loan_type not in scheme['type'].lower():
                continue
                
            # Check basic eligibility criteria
            if (loan_amount >= scheme['min_amount'] and 
                loan_amount <= scheme['max_amount'] and
                annual_income >= scheme['min_income'] and
                age >= scheme['eligibility']['min_age'] and
                age <= scheme['eligibility']['max_age'] and
                cibil_score >= scheme['eligibility']['cibil_score']):
                
                # Check employment type
                if employment_type in scheme['eligibility']['employment']:
                    recommended_schemes.append({
                        'scheme_id': scheme_id,
                        'scheme_data': scheme,
                        'match_score': calculate_scheme_match_score(application_data, scheme)
                    })
        
        # Sort by match score (highest first)
        recommended_schemes.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommended_schemes[:3]  # Return top 3 schemes
        
    except Exception as e:
        print(f"Error getting recommended schemes: {e}")
        return []

def calculate_scheme_match_score(application_data, scheme):
    """Calculate how well a scheme matches the application"""
    score = 0
    
    try:
        loan_amount = float(application_data.get('loan-amount', 0))
        annual_income = float(application_data.get('annual-income', 0))
        cibil_score = int(application_data.get('cibil-score', 600))
        
        # Income ratio score (lower is better for affordability)
        income_ratio = loan_amount / annual_income
        if income_ratio <= 3:
            score += 30
        elif income_ratio <= 5:
            score += 20
        elif income_ratio <= 7:
            score += 10
        
        # CIBIL score bonus
        if cibil_score >= 800:
            score += 25
        elif cibil_score >= 750:
            score += 20
        elif cibil_score >= 700:
            score += 15
        elif cibil_score >= 650:
            score += 10
        
        # Amount range score
        mid_amount = (scheme['min_amount'] + scheme['max_amount']) / 2
        if abs(loan_amount - mid_amount) / mid_amount <= 0.5:
            score += 20
        
        # Income adequacy score
        if annual_income >= scheme['min_income'] * 2:
            score += 15
        elif annual_income >= scheme['min_income'] * 1.5:
            score += 10
        elif annual_income >= scheme['min_income']:
            score += 5
        
        return min(score, 100)  # Cap at 100
        
    except Exception as e:
        return 0

@app.route('/evaluate-loan-eligibility', methods=['POST'])
def evaluate_loan_eligibility():
    """Evaluate loan eligibility and recommend schemes"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        data = request.json
        user_email = session.get('user_email')
        current_language = data.get('language', 'en')
        
        # Get AI assessment first
        ai_assessment = get_ai_loan_assessment(data, current_language)
        
        # Determine eligibility status
        eligibility_status = determine_eligibility_status(data)
        
        if eligibility_status == 'ELIGIBLE':
            # Get recommended schemes
            recommended_schemes = get_recommended_schemes(data)
            
            response = {
                'success': True,
                'eligible': True,
                'eligibility_status': eligibility_status,
                'ai_assessment': ai_assessment,
                'recommended_schemes': recommended_schemes,
                'message': get_localized_message('eligibility_success', current_language)
            }
        else:
            # Get improvement suggestions
            improvement_suggestions = get_improvement_suggestions(data, current_language)
            
            response = {
                'success': True,
                'eligible': False,
                'eligibility_status': eligibility_status,
                'ai_assessment': ai_assessment,
                'improvement_suggestions': improvement_suggestions,
                'message': get_localized_message('eligibility_failed', current_language)
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_ai_loan_assessment(application_data, language='en'):
    """Get AI assessment of loan application"""
    try:
        if not IBM_ENABLED:
            return get_localized_mock_response('ai_assessment', language)
        
        # Prepare prompt for AI assessment
        prompt = get_localized_ai_prompt('loan_assessment', language, application_data)
        
        # Call Watson AI
        token = get_iam_token()
        if not token:
            return get_localized_mock_response('ai_assessment', language)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        
        response = requests.post(AGENT_ENDPOINT, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            ai_response = response.json()
            assessment = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            return translate_ai_response(assessment, language)
        else:
            return get_localized_mock_response('ai_assessment', language)
            
    except Exception as e:
        print(f"Error getting AI assessment: {e}")
        return get_localized_mock_response('ai_assessment', language)

def determine_eligibility_status(application_data):
    """Determine loan eligibility status based on application data"""
    try:
        annual_income = float(application_data.get('annual-income', 0))
        loan_amount = float(application_data.get('loan-amount', 0))
        cibil_score = int(application_data.get('cibil-score', 600))
        employment_type = application_data.get('employment-type', '')
        
        # Calculate income to loan ratio
        income_ratio = loan_amount / annual_income if annual_income > 0 else float('inf')
        
        # Basic eligibility checks
        if (cibil_score >= 750 and 
            income_ratio <= 5 and 
            annual_income >= 300000 and
            employment_type in ['Salaried', 'Self-employed']):
            return 'ELIGIBLE'
        elif (cibil_score >= 650 and 
              income_ratio <= 7 and 
              annual_income >= 200000):
            return 'CONDITIONALLY_ELIGIBLE'
        else:
            return 'NOT_ELIGIBLE'
            
    except Exception as e:
        return 'NOT_ELIGIBLE'

def get_improvement_suggestions(application_data, language='en'):
    """Get suggestions for improving loan eligibility"""
    suggestions = []
    
    try:
        annual_income = float(application_data.get('annual-income', 0))
        loan_amount = float(application_data.get('loan-amount', 0))
        cibil_score = int(application_data.get('cibil-score', 600))
        
        # CIBIL score suggestions
        if cibil_score < 650:
            suggestions.append(get_localized_message('improve_cibil', language))
        
        # Income suggestions
        if annual_income < 300000:
            suggestions.append(get_localized_message('improve_income', language))
        
        # Loan amount suggestions
        income_ratio = loan_amount / annual_income if annual_income > 0 else float('inf')
        if income_ratio > 7:
            suggestions.append(get_localized_message('reduce_loan_amount', language))
        
        return suggestions
        
    except Exception as e:
        return [get_localized_message('general_improvement', language)]

@app.route('/get-scheme-details', methods=['POST'])
def get_scheme_details():
    """Get detailed information about a specific loan scheme"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        data = request.json
        scheme_id = data.get('scheme_id')
        language = data.get('language', 'en')
        
        if scheme_id not in LOAN_SCHEMES:
            return jsonify({'success': False, 'error': 'Scheme not found'})
        
        scheme = LOAN_SCHEMES[scheme_id]
        
        # Get AI-powered detailed explanation
        ai_explanation = get_ai_scheme_explanation(scheme, language)
        
        response = {
            'success': True,
            'scheme': scheme,
            'ai_explanation': ai_explanation
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_ai_scheme_explanation(scheme, language='en'):
    """Get AI explanation of loan scheme"""
    try:
        if not IBM_ENABLED:
            return get_localized_mock_response('scheme_explanation', language)
        
        prompt = get_localized_ai_prompt('scheme_explanation', language, scheme)
        
        token = get_iam_token()
        if not token:
            return get_localized_mock_response('scheme_explanation', language)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800
        }
        
        response = requests.post(AGENT_ENDPOINT, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            ai_response = response.json()
            explanation = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            return translate_ai_response(explanation, language)
        else:
            return get_localized_mock_response('scheme_explanation', language)
            
    except Exception as e:
        print(f"Error getting AI scheme explanation: {e}")
        return get_localized_mock_response('scheme_explanation', language)

@app.route('/submit-scheme-application', methods=['POST'])
def submit_scheme_application():
    """Submit loan application for selected scheme"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        data = request.json
        user_email = session.get('user_email')
        scheme_id = data.get('scheme_id')
        application_data = data.get('application_data')
        
        if scheme_id not in LOAN_SCHEMES:
            return jsonify({'success': False, 'error': 'Invalid scheme'})
        
        scheme = LOAN_SCHEMES[scheme_id]
        
        # Generate application ID
        application_id = str(uuid.uuid4())[:8].upper()
        
        # Save application with scheme details
        application_record = {
            'application_id': application_id,
            'userEmail': user_email,
            'scheme_id': scheme_id,
            'scheme_name': scheme['name'],
            'loan_type': scheme['type'],
            'status': 'PENDING_DOCUMENTS',
            'required_documents': ', '.join(scheme['documents']),
            'submitted_at': datetime.now().isoformat(),
            **application_data
        }
        
        # Save to CSV
        save_scheme_application(application_record)
        
        # Create user alert
        create_user_alert(
            user_email,
            'application_submitted',
            f'Scheme Application Submitted - {application_id}',
            f'Your application for {scheme["name"]} has been submitted. Please upload required documents to proceed.'
        )
        
        response = {
            'success': True,
            'application_id': application_id,
            'scheme': scheme,
            'required_documents': scheme['documents'],
            'message': f'Application {application_id} submitted successfully for {scheme["name"]}'
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def save_scheme_application(application_data):
    """Save scheme-based application to CSV"""
    try:
        # Create comprehensive loans CSV if it doesn't exist
        if not os.path.exists(COMPREHENSIVE_LOANS_CSV):
            with open(COMPREHENSIVE_LOANS_CSV, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'application_id', 'userEmail', 'scheme_id', 'scheme_name', 'loan_type',
                    'status', 'required_documents', 'submitted_at', 'full-name', 'date-of-birth',
                    'gender', 'marital-status', 'nationality', 'contact-number', 'employment-type',
                    'employer-name', 'annual-income', 'existing-loans', 'loan-amount', 'loan-tenure',
                    'loan-purpose', 'preferred-emi', 'cibil-score'
                ])
                writer.writeheader()
        
        # Append new application
        with open(COMPREHENSIVE_LOANS_CSV, 'a', newline='', encoding='utf-8') as file:
            fieldnames = [
                'application_id', 'userEmail', 'scheme_id', 'scheme_name', 'loan_type',
                'status', 'required_documents', 'submitted_at', 'full-name', 'date-of-birth',
                'gender', 'marital-status', 'nationality', 'contact-number', 'employment-type',
                'employer-name', 'annual-income', 'existing-loans', 'loan-amount', 'loan-tenure',
                'loan-purpose', 'preferred-emi', 'cibil-score'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(application_data)
            
    except Exception as e:
        print(f"Error saving scheme application: {e}")
        raise e
@app.route('/apply-comprehensive-loan', methods=['POST'])
def apply_comprehensive_loan():
    """Handle comprehensive loan application - now redirects to new evaluation system"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        data = request.json
        data['userEmail'] = session.get('user_email')  # Add user email from session
        
        # Redirect to new evaluation endpoint
        return evaluate_loan_eligibility()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/user-alerts', methods=['GET'])
def get_user_alerts_endpoint():
    """Get all alerts for logged-in user"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        user_email = session.get('user_email')
        alerts = get_user_alerts(user_email)
        return jsonify({'success': True, 'alerts': alerts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload-documents', methods=['POST'])
def upload_documents():
    """Handle document upload for loan applications"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        application_id = request.form.get('application_id')
        document_type = request.form.get('document_type')
        user_email = session.get('user_email')
        
        if not application_id or not document_type:
            return jsonify({'success': False, 'error': 'Application ID and document type required'})
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(CSV_DIR, 'uploads', application_id)
        os.makedirs(uploads_dir, exist_ok=True)
        
        uploaded_files = []
        
        # Process the uploaded file
        if 'document' in request.files:
            file = request.files['document']
            if file and file.filename:
                # Secure filename
                filename = f"{document_type}_{file.filename}"
                file_path = os.path.join(uploads_dir, filename)
                
                try:
                    file.save(file_path)
                    
                    # Save to database
                    save_document_upload(application_id, user_email, document_type, filename, file_path)
                    uploaded_files.append(filename)
                    
                except Exception as e:
                    print(f"Error saving file {filename}: {e}")
                    return jsonify({'success': False, 'error': f'Error saving file: {str(e)}'})
        
        if uploaded_files:
            # Update application with uploaded documents
            update_uploaded_documents(application_id, uploaded_files)
            
            # Create alert for admin
            create_admin_alert(application_id, 'documents_uploaded', 
                             'Documents Uploaded for Review',
                             f'Application {application_id} has uploaded {document_type} for verification')
            
            # Send email to user
            send_email_notification(
                user_email,
                f"Document Uploaded Successfully - Application {application_id}",
                f"Your {document_type} has been successfully uploaded for application {application_id}. Our team will review it shortly and contact you if any additional information is needed.",
                'document_upload'
            )
            
            return jsonify({
                'success': True, 
                'message': f'Successfully uploaded {document_type}',
                'files': uploaded_files
            })
        else:
            return jsonify({'success': False, 'error': 'No valid files uploaded'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/notify-admin-document-upload', methods=['POST'])
def notify_admin_document_upload():
    """Send email notification to admin when documents are uploaded"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        data = request.json
        application_id = data.get('application_id')
        document_type = data.get('document_type')
        user_email = data.get('user_email')
        
        if not all([application_id, document_type, user_email]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Get admin email (you can configure this)
        admin_email = "singhishant37@gmail.com"  # Change this to actual admin email
        
        # Create admin alert
        create_admin_alert(
            application_id, 
            'document_uploaded',
            f'New Document Uploaded - {document_type}',
            f'User {user_email} has uploaded {document_type} for application {application_id}. Please review and verify the document.'
        )
        
        # Send email to admin
        admin_subject = f"🔔 Document Upload Alert - Application {application_id}"
        admin_message = f"""A new document has been uploaded for review.

Application Details:
• Application ID: {application_id}
• User Email: {user_email}
• Document Type: {document_type}
• Upload Time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Action Required:
Please log in to the admin dashboard to review and verify the uploaded document.

Direct Link: http://127.0.0.1:5001/staff.html

Best regards,
AI Banking Portal System"""

        html_content = create_html_email_template(
            title="New Document Upload",
            content=f"""A user has uploaded a new document for verification.

Application ID: {application_id}
User: {user_email}
Document: {document_type}

Please review the document in your admin dashboard.""",
            cta_text="Review Document",
            cta_link="http://127.0.0.1:5001/staff.html",
            alert_type="info"
        )
        
        send_email_notification(admin_email, admin_subject, admin_message, 'admin_alert', html_content)
        
        return jsonify({'success': True, 'message': 'Admin notified successfully'})
        
    except Exception as e:
        print(f"Error notifying admin: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/application-details/<application_id>', methods=['GET'])
def get_application_details(application_id):
    """Get detailed application information including documents"""
    try:
        if not session.get('user_logged_in'):
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        user_email = session.get('user_email')
        
        # Get application details
        with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['application_id'] == application_id and row['user_email'] == user_email:
                    # Get associated documents
                    documents = get_application_documents(application_id)
                    
                    return jsonify({
                        'success': True,
                        'application': row,
                        'documents': documents
                    })
        
        return jsonify({'success': False, 'error': 'Application not found'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/applications', methods=['GET'])
def admin_get_applications():
    """Get all applications for admin review"""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Admin authentication required'})
        
        applications = []
        
        # Get comprehensive applications
        try:
            with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Get associated documents count
                    documents = get_application_documents(row['application_id'])
                    row['document_count'] = len(documents)
                    applications.append(row)
        except FileNotFoundError:
            pass
        
        return jsonify({'success': True, 'applications': applications})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/verify-application', methods=['POST'])
def admin_verify_application():
    """Admin endpoint to verify/approve/reject applications"""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Admin authentication required'})
        
        data = request.json
        application_id = data.get('application_id')
        action = data.get('action')  # 'approve', 'reject', 'request_revision'
        admin_notes = data.get('admin_notes', '')
        
        if not application_id or not action:
            return jsonify({'success': False, 'error': 'Application ID and action required'})
        
        # Get application details for email notification
        application_data = None
        with open(COMPREHENSIVE_LOANS_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['application_id'] == application_id:
                    application_data = row
                    break
        
        if not application_data:
            return jsonify({'success': False, 'error': 'Application not found'})
        
        user_email = application_data['user_email']
        user_name = application_data['full_name']
        
        # Update application status
        if action == 'approve':
            success = update_application_status(application_id, 'approved', admin_notes, 'verified')
            
            # Send approval notification
            create_user_alert(
                user_email, application_id, 'approval',
                'Loan Application Approved!',
                f'Congratulations! Your loan application {application_id} has been approved.',
                'high'
            )
            
            email_subject = f"🎉 Loan Approved - Application {application_id}"
            email_message = f"""Dear {user_name},

Congratulations! Your loan application has been APPROVED after thorough review and document verification.

Application Details:
• Application ID: {application_id}
• Loan Type: {application_data.get('loan_type', 'N/A')}
• Loan Amount: {format_currency(application_data.get('loan_amount', 'N/A'))}
• Status: APPROVED

Admin Review Notes: {admin_notes}

Next Steps:
1. You will receive loan agreement documents via email within 24 hours
2. Please review and digitally sign the loan agreement
3. Loan disbursement will be processed within 3-5 business days after agreement completion
4. Our relationship manager will contact you to complete the process

Thank you for choosing AI Banking Portal for your financial needs.

Best regards,
AI Banking Portal Team"""

            html_content = create_html_email_template(
                title="Loan Application Approved!",
                content=f"""Your loan application has been successfully approved after document verification.

Application ID: {application_id}
Loan Amount: {format_currency(application_data.get('loan_amount', 'N/A'))}
Status: APPROVED

Admin Notes: {admin_notes}

Next Steps:
• Loan agreement documents will be sent within 24 hours
• Digital signature required
• Disbursement within 3-5 business days""",
                cta_text="View Application Status",
                cta_link="http://127.0.0.1:5001/",
                alert_type="success"
            )
            
            send_email_notification(
                user_email, email_subject, email_message, 'approval', html_content
            )
            
        elif action == 'reject':
            success = update_application_status(application_id, 'rejected', admin_notes, 'rejected')
            
            # Send rejection notification
            create_user_alert(
                user_email, application_id, 'rejection',
                'Loan Application Decision',
                f'Your loan application {application_id} has been reviewed. Please check your email for details.',
                'high'
            )
            
            email_subject = f"📋 Loan Application Decision - Application {application_id}"
            email_message = f"""Dear {user_name},

After careful review of your loan application and submitted documents, we are unable to approve your request at this time.

Application Details:
• Application ID: {application_id}
• Loan Type: {application_data.get('loan_type', 'N/A')}
• Loan Amount: {format_currency(application_data.get('loan_amount', 'N/A'))}
• Status: NOT APPROVED

Review Notes: {admin_notes}

We understand this may be disappointing, and we want to help you succeed in future applications:

• You may reapply after addressing the mentioned concerns
• Our customer service team is available to discuss improvement strategies
• Consider applying for a smaller loan amount or improving your credit profile

We appreciate your interest in our services and hope to serve you in the future.

Best regards,
AI Banking Portal Team"""

            html_content = create_html_email_template(
                title="Loan Application Decision",
                content=f"""After thorough review, we are unable to approve your loan application at this time.

Application ID: {application_id}
Status: NOT APPROVED

Review Notes:
{admin_notes}

We encourage you to:
• Address the mentioned concerns
• Consider reapplying with improved documentation
• Contact our team for guidance on eligibility improvement""",
                cta_text="Contact Customer Service",
                cta_link="http://127.0.0.1:5001/",
                alert_type="danger"
            )
            
            send_email_notification(
                user_email, email_subject, email_message, 'rejection', html_content
            )
            
        elif action == 'request_revision':
            success = update_application_status(application_id, 'revision_requested', admin_notes, 'revision_required')
            
            # Send revision request notification
            create_user_alert(
                user_email, application_id, 'revision_required',
                'Application Revision Required',
                f'Your loan application {application_id} requires additional information or corrected documents.',
                'medium'
            )
            
            email_subject = f"📝 Additional Information Required - Application {application_id}"
            email_message = f"""Dear {user_name},

Your loan application has been reviewed and we need additional information or document corrections to proceed.

Application Details:
• Application ID: {application_id}
• Loan Type: {application_data.get('loan_type', 'N/A')}
• Loan Amount: {format_currency(application_data.get('loan_amount', 'N/A'))}
• Status: REVISION REQUIRED

Required Changes: {admin_notes}

Next Steps:
1. Log in to your account dashboard
2. Review the specific requirements mentioned above
3. Upload corrected or additional documents as needed
4. Resubmit your application for review

Our team will prioritize the review of your updated application.

Best regards,
AI Banking Portal Team"""

            html_content = create_html_email_template(
                title="Application Revision Required",
                content=f"""We need additional information to complete the review of your loan application.

Application ID: {application_id}
Status: REVISION REQUIRED

Required Changes:
{admin_notes}

Please log in to your dashboard and provide the requested information or corrected documents.""",
                cta_text="Update Application",
                cta_link="http://127.0.0.1:5001/",
                alert_type="warning"
            )
            
            send_email_notification(
                user_email, email_subject, email_message, 'revision_request', html_content
            )
        
        if success:
            return jsonify({'success': True, 'message': f'Application {action}d successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update application'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/')
def serve_main():
    """Serve the main LoanBot chatbot interface"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/staff')
def serve_staff():
    """Serve the staff login page"""
    return send_from_directory('../frontend', 'staff.html')

@app.route('/apply')
def serve_apply():
    """Serve the loan application page"""
    return send_from_directory('../frontend', 'apply.html')

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Banking Portal is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

# Initialize CSV files on startup
initialize_csv_files()

# --- Main Execution ---
if __name__ == "__main__":
    # For Render deployment - use PORT environment variable
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)