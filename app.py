import os
import json
import logging
import uuid
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
from utils.parsers import parse_sonarqube_report, parse_sbom_report, parse_trivy_report, parse_trivy_html_report
from utils.sonarqube_client import fetch_sonarqube_data
from models import db, Project, Report

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS
CORS(app)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json', 'xml', 'html'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_project(name: str) -> str:
    """Create a new project and return its ID"""
    project_id = str(uuid.uuid4())
    project = Project(id=project_id, name=name)
    db.session.add(project)
    db.session.commit()
    return project_id

@app.route('/')
def home():
    """Home page showing all projects"""
    # Get projects based on user permissions
    if is_admin():
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        projects = get_user_projects()
    
    projects_dict = {project.id: project.to_dict() for project in projects}
    
    # Pass user context to template
    user_context = {
        'is_admin': is_admin(),
        'total_projects': len(projects_dict)
    }
    
    return render_template('home.html', projects=projects_dict, user=user_context)

@app.route('/create-project', methods=['GET', 'POST'])
def create_project_route():
    """Create a new project"""
    # Check admin permissions
    if not is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('home'))
    
    user_context = {
        'is_admin': is_admin()
    }
    
    if request.method == 'POST':
        project_name = request.form.get('project_name', '').strip()
        if not project_name:
            return jsonify({'success': False, 'message': 'Project name is required.'}), 400
        
        project_id = create_project(project_name)
        return jsonify({
            'success': True, 
            'message': f'Project "{project_name}" created successfully.',
            'redirect_url': url_for('project_dashboard', project_id=project_id)
        })
    
    return render_template('create_project.html', user=user_context)

@app.route('/project/<project_id>')
def project_dashboard(project_id):
    """Project dashboard page"""
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    user_context = {
        'is_admin': is_admin()
    }
    
    return render_template('project_dashboard.html', project=project.to_dict(), user=user_context)

@app.route('/project/<project_id>/upload', methods=['POST'])
def upload_file(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    report_type = request.form.get('report_type')
    
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    if not report_type or report_type not in ['sonarqube', 'sbom', 'trivy']:
        return jsonify({'error': 'Invalid report type'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Parse the file based on report type and file extension
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            parsed_data = None
            if report_type == 'sonarqube':
                parsed_data = parse_sonarqube_report(file_content)
            elif report_type == 'sbom':
                parsed_data = parse_sbom_report(file_content)
            elif report_type == 'trivy':
                # Check if it's HTML or JSON
                if filename.lower().endswith('.html'):
                    parsed_data = parse_trivy_html_report(file_content)
                else:
                    parsed_data = parse_trivy_report(file_content)
            
            # Store parsed data in database
            project.set_report(report_type, parsed_data)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True, 
                'message': f'{report_type.title()} report processed successfully',
                'data': parsed_data
            })
            
        except Exception as e:
            logging.error(f"Error processing {report_type} file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload JSON, XML, or HTML files.'}), 400

@app.route('/project/<project_id>/api/summary')
def get_project_summary(project_id):
    """Get summary data for the project dashboard"""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project_data = project.to_dict()
    reports = project_data['reports']
    
    summary = {
        'sonarqube': reports.get('sonarqube'),
        'sbom': reports.get('sbom'),
        'trivy': reports.get('trivy'),
        'total_reports': sum(1 for report in reports.values() if report is not None)
    }
    return jsonify(summary)

@app.route('/project/<project_id>/sonarqube')
def project_sonarqube_detail(project_id):
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    project_data = project.to_dict()
    sonarqube_data = project_data['reports'].get('sonarqube')
    
    user_context = {
        'is_admin': is_admin()
    }
    
    return render_template('sonarqube_detail.html', 
                         data=sonarqube_data, 
                         project=project,
                         user=user_context)

@app.route('/project/<project_id>/sbom')
def project_sbom_detail(project_id):
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    project_data = project.to_dict()
    sbom_data = project_data['reports'].get('sbom')
    
    user_context = {
        'is_admin': is_admin()
    }
    
    return render_template('sbom_detail.html', 
                         data=sbom_data, 
                         project=project,
                         user=user_context)

@app.route('/project/<project_id>/trivy')
def project_trivy_detail(project_id):
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    project_data = project.to_dict()
    trivy_data = project_data['reports'].get('trivy')
    
    user_context = {
        'is_admin': is_admin()
    }
    
    return render_template('trivy_detail.html', 
                         data=trivy_data, 
                         project=project,
                         user=user_context)

@app.route('/project/<project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    # Check admin permissions
    if not is_admin():
        return jsonify({'success': False, 'message': 'Access denied. Administrator privileges required.'}), 403
    
    project = Project.query.get(project_id)
    if project:
        project_name = project.name
        db.session.delete(project)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Project "{project_name}" deleted successfully.',
            'redirect_url': url_for('home')
        })
    else:
        return jsonify({'success': False, 'message': 'Project not found.'}), 404

@app.route('/health')
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/api/projects/find-or-create', methods=['POST'])
def find_or_create_project():
    """Find existing project by name or create new one - for Jenkins integration"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Project name is required'}), 400
    
    project_name = data['name'].strip()
    if not project_name:
        return jsonify({'error': 'Project name cannot be empty'}), 400
    
    # Try to find existing project by name
    existing_project = Project.query.filter_by(name=project_name).first()
    if existing_project:
        return jsonify({
            'project_id': existing_project.id,
            'name': existing_project.name,
            'created': False,
            'created_at': existing_project.created_at.isoformat()
        }), 200
    
    # Create new project
    try:
        project_id = create_project(project_name)
        project = Project.query.get(project_id)
        return jsonify({
            'project_id': project.id,
            'name': project.name,
            'created': True,
            'created_at': project.created_at.isoformat()
        }), 201
    except Exception as e:
        logging.error(f"Error creating project: {str(e)}")
        return jsonify({'error': 'Failed to create project'}), 500

@app.route('/api/projects/<project_id>/status')
def get_project_status(project_id):
    """Get project status - for Jenkins integration"""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project_data = project.to_dict()
    reports = project_data['reports']
    
    status = {
        'project_id': project.id,
        'name': project.name,
        'created_at': project.created_at.isoformat(),
        'updated_at': project.updated_at.isoformat(),
        'reports_status': {
            'sonarqube': {
                'uploaded': reports.get('sonarqube') is not None,
                'last_updated': None
            },
            'sbom': {
                'uploaded': reports.get('sbom') is not None,
                'last_updated': None
            },
            'trivy': {
                'uploaded': reports.get('trivy') is not None,
                'last_updated': None
            }
        },
        'total_reports': sum(1 for report in reports.values() if report is not None)
    }
    
    # Add last updated timestamps for each report type
    for report_type in ['sonarqube', 'sbom', 'trivy']:
        report = project.get_report(report_type)
        if report:
            status['reports_status'][report_type]['last_updated'] = report.updated_at.isoformat()
    
    return jsonify(status), 200

@app.route('/api/projects/<project_id>/webhook', methods=['POST'])
def project_webhook(project_id):
    """Webhook endpoint for external integrations like Jenkins"""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    event_type = data.get('event', 'unknown')
    
    logging.info(f"Webhook received for project {project_id}: {event_type}")
    
    # Update project timestamp
    project.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'status': 'received',
        'project_id': project_id,
        'event': event_type,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/projects/<project_id>/sonarqube/fetch', methods=['POST'])
def fetch_sonarqube_data_api(project_id):
    """Fetch SonarQube data directly from server API"""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # Extract SonarQube connection details
    sonar_url = data.get('sonar_url')
    sonar_token = data.get('sonar_token') 
    sonar_project_key = data.get('sonar_project_key')
    
    if not all([sonar_url, sonar_token, sonar_project_key]):
        return jsonify({
            'error': 'Missing required fields',
            'required': ['sonar_url', 'sonar_token', 'sonar_project_key']
        }), 400
    
    try:
        # Fetch data from SonarQube API
        sonar_data = fetch_sonarqube_data(sonar_url, sonar_token, sonar_project_key)
        
        # Store in database
        project.set_report('sonarqube', sonar_data)
        
        return jsonify({
            'success': True,
            'message': 'SonarQube data fetched and stored successfully',
            'project_name': sonar_data.get('project_name'),
            'last_analysis': sonar_data.get('last_analysis'),
            'metrics_summary': {
                'bugs': sonar_data.get('bugs', 0),
                'vulnerabilities': sonar_data.get('vulnerabilities', 0),
                'code_smells': sonar_data.get('code_smells', 0),
                'coverage': sonar_data.get('coverage', 0),
                'quality_gate': sonar_data.get('quality_gate_status', 'UNKNOWN')
            }
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error fetching SonarQube data: {error_msg}")
        
        # Provide user-friendly error messages based on the error type
        if "Access denied" in error_msg or "403" in error_msg:
            return jsonify({
                'error': 'Access Denied',
                'message': 'Your SonarQube token does not have sufficient permissions.',
                'suggestions': [
                    'Verify your token has "Browse" permission for this project',
                    'Check that the project key is correct',
                    'Ensure your token is valid and not expired',
                    'Contact your SonarQube administrator for proper permissions'
                ],
                'details': error_msg
            }), 403
        elif "not found" in error_msg.lower() or "404" in error_msg:
            return jsonify({
                'error': 'Project Not Found',
                'message': f'The project "{sonar_project_key}" was not found in SonarQube.',
                'suggestions': [
                    'Verify the project key is spelled correctly',
                    'Check that the project exists in your SonarQube instance',
                    'Ensure you have access to view this project'
                ],
                'details': error_msg
            }), 404
        elif "Authentication failed" in error_msg or "401" in error_msg:
            return jsonify({
                'error': 'Authentication Failed',
                'message': 'Invalid SonarQube token or credentials.',
                'suggestions': [
                    'Verify your SonarQube token is correct',
                    'Generate a new token if the current one has expired',
                    'Ensure the token format is correct (starts with squ_)'
                ],
                'details': error_msg
            }), 401
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            return jsonify({
                'error': 'Connection Error',
                'message': 'Unable to connect to SonarQube server.',
                'suggestions': [
                    'Check that the SonarQube URL is correct and accessible',
                    'Verify your network connection',
                    'Ensure the SonarQube server is running and accessible'
                ],
                'details': error_msg
            }), 503
        else:
            return jsonify({
                'error': 'SonarQube Integration Error',
                'message': 'An unexpected error occurred while connecting to SonarQube.',
                'details': error_msg
            }), 500

@app.route('/api/sonarqube/test-connection', methods=['POST'])
def test_sonarqube_connection():
    """Test SonarQube server connection"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    sonar_url = data.get('sonar_url')
    sonar_token = data.get('sonar_token')
    
    if not all([sonar_url, sonar_token]):
        return jsonify({
            'error': 'Missing required fields',
            'required': ['sonar_url', 'sonar_token']
        }), 400
    
    try:
        from utils.sonarqube_client import SonarQubeClient
        client = SonarQubeClient(sonar_url, sonar_token)
        
        if client.test_connection():
            # Get system info for version
            response = client.session.get(f"{sonar_url}/api/system/status")
            system_info = response.json() if response.ok else {}
            
            return jsonify({
                'success': True,
                'message': 'Connection successful',
                'version': system_info.get('version', 'Unknown'),
                'status': system_info.get('status', 'UP')
            }), 200
        else:
            return jsonify({
                'error': 'Connection failed',
                'message': 'Unable to connect to SonarQube server'
            }), 503
    except Exception as e:
        return jsonify({
            'error': 'Connection test failed',
            'details': str(e)
        }), 500

@app.route('/api/sonarqube/save-config', methods=['POST'])
def save_sonarqube_config():
    """Save global SonarQube configuration to session"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    sonar_url = data.get('sonar_url')
    sonar_token = data.get('sonar_token')
    refresh_interval = data.get('refresh_interval', 900)  # Default 15 minutes
    
    if not sonar_url:
        return jsonify({'error': 'SonarQube URL is required'}), 400
    
    # Store in session
    session['sonar_url'] = sonar_url
    session['sonar_refresh_interval'] = refresh_interval
    if sonar_token:
        session['sonar_token'] = sonar_token
    
    return jsonify({
        'success': True,
        'message': 'Configuration saved successfully'
    }), 200

@app.route('/api/sonarqube/get-global-config', methods=['GET'])
def get_global_sonarqube_config():
    """Get global SonarQube configuration from session"""
    return jsonify({
        'sonar_url': session.get('sonar_url', ''),
        'has_token': bool(session.get('sonar_token'))
    }), 200

@app.route('/configuration')
def configuration():
    """Configuration page"""
    # Check admin permissions
    if not is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('home'))
    
    # Get current SonarQube configuration from session
    sonarqube_config = {
        'sonar_url': session.get('sonar_url', ''),
        'has_token': bool(session.get('sonar_token')),
        'refresh_interval': session.get('sonar_refresh_interval', 900)
    }
    
    # Pass user context to template
    user_context = {
        'is_admin': is_admin()
    }
    
    return render_template('configuration.html', sonarqube_config=sonarqube_config, user=user_context)

@app.route('/api/sso/test-connection', methods=['POST'])
def test_sso_connection():
    """Test SSO connection configuration"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    provider = data.get('provider')
    
    try:
        if provider == 'gitlab':
            url = data.get('url')
            client_id = data.get('client_id')
            if not all([url, client_id]):
                return jsonify({'error': 'GitLab URL and Client ID are required'}), 400
            
            # Test GitLab OAuth endpoint
            test_url = f"{url.rstrip('/')}/oauth/applications"
            response = requests.get(f"{url.rstrip('/')}/api/v4/user", timeout=10)
            
            return jsonify({
                'success': True,
                'details': f'GitLab instance accessible at {url}',
                'api_version': 'v4'
            })
            
        elif provider == 'keycloak':
            url = data.get('url')
            realm = data.get('realm')
            if not all([url, realm]):
                return jsonify({'error': 'Keycloak URL and Realm are required'}), 400
            
            # Test Keycloak realm endpoint
            test_url = f"{url.rstrip('/')}/realms/{realm}/.well-known/openid_configuration"
            response = requests.get(test_url, timeout=10)
            
            if response.ok:
                config = response.json()
                return jsonify({
                    'success': True,
                    'details': f'Keycloak realm "{realm}" is accessible',
                    'issuer': config.get('issuer')
                })
            else:
                return jsonify({'error': f'Keycloak realm not found: {response.status_code}'}), 400
                
        elif provider == 'azure':
            tenant_id = data.get('tenant_id')
            if not tenant_id:
                return jsonify({'error': 'Azure Tenant ID is required'}), 400
            
            # Test Azure AD tenant endpoint
            test_url = f"https://login.microsoftonline.com/{tenant_id}/.well-known/openid_configuration"
            response = requests.get(test_url, timeout=10)
            
            if response.ok:
                config = response.json()
                return jsonify({
                    'success': True,
                    'details': f'Azure AD tenant "{tenant_id}" is accessible',
                    'issuer': config.get('issuer')
                })
            else:
                return jsonify({'error': f'Azure AD tenant not found: {response.status_code}'}), 400
        
        else:
            return jsonify({'error': 'Unsupported SSO provider'}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Connection failed',
            'details': str(e)
        }), 503
    except Exception as e:
        return jsonify({
            'error': 'SSO test failed',
            'details': str(e)
        }), 500

@app.route('/api/sso/save-config', methods=['POST'])
def save_sso_config():
    """Save SSO configuration"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    provider = data.get('provider')
    if not provider:
        return jsonify({'error': 'SSO provider is required'}), 400
    
    # Store SSO configuration in session (in production, use database)
    session['sso_config'] = data
    session['sso_enabled'] = True
    
    return jsonify({
        'success': True,
        'message': f'{provider.capitalize()} SSO configuration saved successfully'
    }), 200

def is_admin():
    """Check if current user has admin privileges"""
    # For now, assume admin based on session flag
    # In production, this would check against SSO groups/roles
    return session.get('is_admin', True)  # Default to admin for demo

def get_user_projects():
    """Get projects accessible to current user"""
    if is_admin():
        # Admins see all projects
        return Project.query.all()
    else:
        # Regular users see only assigned projects
        user_id = session.get('user_id')
        if not user_id:
            return []
        
        # In production, filter by user assignments
        # For now, return empty list for non-admin users
        return []

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/projects/<project_id>/sonarqube/connect', methods=['POST'])
def connect_project_sonarqube(project_id):
    """Connect project to SonarQube using project key and global config"""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    project_key = data.get('project_key')
    if not project_key:
        return jsonify({'error': 'Project key is required'}), 400
    
    # Get global configuration
    sonar_url = session.get('sonar_url')
    sonar_token = session.get('sonar_token')
    
    if not sonar_url:
        return jsonify({
            'error': 'Global SonarQube configuration not found',
            'message': 'Please configure SonarQube server first'
        }), 400
    
    if not sonar_token:
        return jsonify({
            'error': 'SonarQube token not configured',
            'message': 'Please provide a token in global configuration'
        }), 400
    
    try:
        # Save project key
        project.sonar_project_key = project_key
        db.session.commit()
        
        # Fetch data from SonarQube API
        sonar_data = fetch_sonarqube_data(sonar_url, sonar_token, project_key)
        
        # Store in database
        project.set_report('sonarqube', sonar_data)
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to SonarQube',
            'project_name': sonar_data.get('project_name'),
            'project_key': project_key
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error connecting project to SonarQube: {error_msg}")
        
        # Provide user-friendly error messages
        if "Access denied" in error_msg or "403" in error_msg:
            return jsonify({
                'error': 'Access denied to SonarQube project',
                'message': 'Your token does not have permission to access this project'
            }), 403
        elif "not found" in error_msg.lower() or "404" in error_msg:
            return jsonify({
                'error': 'Project not found in SonarQube',
                'message': f'Project key "{project_key}" was not found'
            }), 404
        else:
            return jsonify({
                'error': 'Connection failed',
                'message': 'Unable to connect to SonarQube. Check your configuration.'
            }), 500

# Security Heatmap Routes
@app.route('/security-heatmap')
def security_heatmap():
    """Security Risk Heatmap page"""
    return render_template('security_heatmap.html')

@app.route('/api/security-heatmap/data')
def get_heatmap_data():
    """Get security heatmap data from real project data"""
    try:
        projects = Project.query.all()
        heatmap_data = {
            'projects': [],
            'statistics': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'trendScore': 0,
                'criticalChange': 0,
                'highChange': 0,
                'mediumChange': 0,
                'trendDirection': 'Stable'
            }
        }
        
        total_critical = 0
        total_high = 0
        total_medium = 0
        total_low = 0
        
        for project in projects:
            # Get all reports for this project
            sonarqube_report = project.get_report('sonarqube')
            sbom_report = project.get_report('sbom')
            trivy_report = project.get_report('trivy')
            
            # Calculate risk scores for each category
            risks = {
                'vulnerabilities': calculate_vulnerability_risk(trivy_report, sbom_report),
                'code_quality': calculate_code_quality_risk(sonarqube_report),
                'dependencies': calculate_dependency_risk(sbom_report),
                'containers': calculate_container_risk(trivy_report)
            }
            
            # Calculate severity counts
            counts = calculate_severity_counts(sonarqube_report, sbom_report, trivy_report)
            
            # Determine trend based on recent changes
            trend = calculate_risk_trend(project)
            
            project_data = {
                'name': project.name,
                'id': project.id,
                'risks': risks,
                'counts': counts,
                'trend': trend,
                'lastUpdated': project.updated_at.isoformat() if project.updated_at else None
            }
            
            heatmap_data['projects'].append(project_data)
            
            # Aggregate statistics
            total_critical += counts.get('critical', 0)
            total_high += counts.get('high', 0)
            total_medium += counts.get('medium', 0)
            total_low += counts.get('low', 0)
        
        # Update global statistics
        heatmap_data['statistics']['critical'] = total_critical
        heatmap_data['statistics']['high'] = total_high
        heatmap_data['statistics']['medium'] = total_medium
        heatmap_data['statistics']['low'] = total_low
        heatmap_data['statistics']['trendScore'] = calculate_overall_trend_score(heatmap_data['projects'])
        
        return jsonify({'success': True, 'data': heatmap_data})
        
    except Exception as e:
        print(f"Error generating heatmap data: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/security-heatmap/timeline')
def get_heatmap_timeline():
    """Get timeline data for risk visualization"""
    try:
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Generate hourly data points
        timeline_data = {
            'labels': [],
            'critical': [],
            'high': [],
            'medium': []
        }
        
        current_time = start_time
        while current_time <= end_time:
            timeline_data['labels'].append(current_time.strftime('%H:%M'))
            
            # Calculate actual risk counts at this time
            projects = Project.query.all()
            critical_count = 0
            high_count = 0
            medium_count = 0
            
            for project in projects:
                # Get current severity counts
                sonarqube_report = project.get_report('sonarqube')
                sbom_report = project.get_report('sbom')
                trivy_report = project.get_report('trivy')
                
                counts = calculate_severity_counts(sonarqube_report, sbom_report, trivy_report)
                critical_count += counts.get('critical', 0)
                high_count += counts.get('high', 0)
                medium_count += counts.get('medium', 0)
            
            timeline_data['critical'].append(critical_count)
            timeline_data['high'].append(high_count)
            timeline_data['medium'].append(medium_count)
            
            current_time += timedelta(hours=1)
        
        return jsonify({'success': True, 'data': timeline_data})
        
    except Exception as e:
        print(f"Error generating timeline data: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/security-heatmap/details/<project_id>/<category>')
def get_risk_details(project_id, category):
    """Get detailed risk information for a specific project and category"""
    try:
        project = Project.query.get_or_404(project_id)
        
        details = {
            'project': project.name,
            'category': category,
            'issues': [],
            'recommendations': []
        }
        
        if category == 'vulnerabilities':
            trivy_report = project.get_report('trivy')
            if trivy_report:
                trivy_data = json.loads(trivy_report.data)
                details['issues'] = extract_vulnerability_details(trivy_data)
                details['recommendations'] = get_vulnerability_recommendations(trivy_data)
        
        elif category == 'code_quality':
            sonarqube_report = project.get_report('sonarqube')
            if sonarqube_report:
                sonar_data = json.loads(sonarqube_report.data)
                details['issues'] = extract_code_quality_details(sonar_data)
                details['recommendations'] = get_code_quality_recommendations(sonar_data)
        
        elif category == 'dependencies':
            sbom_report = project.get_report('sbom')
            if sbom_report:
                sbom_data = json.loads(sbom_report.data)
                details['issues'] = extract_dependency_details(sbom_data)
                details['recommendations'] = get_dependency_recommendations(sbom_data)
        
        elif category == 'containers':
            trivy_report = project.get_report('trivy')
            if trivy_report:
                trivy_data = json.loads(trivy_report.data)
                details['issues'] = extract_container_details(trivy_data)
                details['recommendations'] = get_container_recommendations(trivy_data)
        
        return jsonify({'success': True, 'data': details})
        
    except Exception as e:
        print(f"Error getting risk details: {e}")
        return jsonify({'success': False, 'message': str(e)})

# Helper functions for risk calculations
def calculate_vulnerability_risk(trivy_report, sbom_report):
    """Calculate vulnerability risk score (0-10)"""
    if not trivy_report:
        return 0
    
    try:
        trivy_data = json.loads(trivy_report.data)
        vulnerabilities = trivy_data.get('vulnerabilities', [])
        
        if not vulnerabilities:
            return 0
        
        # Count by severity
        critical = sum(1 for v in vulnerabilities if v.get('severity') == 'CRITICAL')
        high = sum(1 for v in vulnerabilities if v.get('severity') == 'HIGH')
        medium = sum(1 for v in vulnerabilities if v.get('severity') == 'MEDIUM')
        
        # Calculate weighted score
        score = min(10, (critical * 3 + high * 2 + medium * 1) / 10)
        return round(score, 1)
    except:
        return 0

def calculate_code_quality_risk(sonarqube_report):
    """Calculate code quality risk score (0-10)"""
    if not sonarqube_report:
        return 0
    
    try:
        sonar_data = json.loads(sonarqube_report.data)
        
        # Extract key metrics
        bugs = sonar_data.get('bugs', 0)
        code_smells = sonar_data.get('code_smells', 0)
        coverage = sonar_data.get('coverage', 100)
        
        # Calculate risk based on metrics
        bug_score = min(5, bugs / 20)  # 20+ bugs = 5 points
        smell_score = min(3, code_smells / 100)  # 100+ smells = 3 points
        coverage_score = max(0, (80 - coverage) / 20)  # Below 80% coverage adds risk
        
        total_score = bug_score + smell_score + coverage_score
        return round(min(10, total_score), 1)
    except:
        return 0

def calculate_dependency_risk(sbom_report):
    """Calculate dependency risk score (0-10)"""
    if not sbom_report:
        return 0
    
    try:
        sbom_data = json.loads(sbom_report.data)
        components = sbom_data.get('components', [])
        
        if not components:
            return 0
        
        # Count outdated/vulnerable dependencies
        vulnerable_count = 0
        total_count = len(components)
        
        for component in components:
            # Check for known vulnerabilities or outdated versions
            if component.get('vulnerabilities') or component.get('outdated'):
                vulnerable_count += 1
        
        # Calculate risk percentage
        risk_percentage = (vulnerable_count / total_count) * 10 if total_count > 0 else 0
        return round(min(10, risk_percentage), 1)
    except:
        return 0

def calculate_container_risk(trivy_report):
    """Calculate container security risk score (0-10)"""
    if not trivy_report:
        return 0
    
    try:
        trivy_data = json.loads(trivy_report.data)
        
        # Look for container-specific issues
        misconfigurations = trivy_data.get('misconfigurations', [])
        secrets = trivy_data.get('secrets', [])
        vulnerabilities = trivy_data.get('vulnerabilities', [])
        
        # Calculate risk from different sources
        config_risk = min(4, len(misconfigurations) / 5)  # Misconfigurations
        secret_risk = min(3, len(secrets))  # Exposed secrets
        vuln_risk = min(3, len([v for v in vulnerabilities if v.get('severity') in ['CRITICAL', 'HIGH']]) / 10)
        
        total_risk = config_risk + secret_risk + vuln_risk
        return round(min(10, total_risk), 1)
    except:
        return 0

def calculate_severity_counts(sonarqube_report, sbom_report, trivy_report):
    """Calculate total severity counts across all reports"""
    counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    # Count from SonarQube
    if sonarqube_report:
        try:
            sonar_data = json.loads(sonarqube_report.data)
            bugs = sonar_data.get('bugs', 0)
            vulnerabilities = sonar_data.get('vulnerabilities', 0)
            
            # Map to severity levels based on SonarQube categorization
            counts['high'] += vulnerabilities
            counts['medium'] += bugs
        except:
            pass
    
    # Count from Trivy
    if trivy_report:
        try:
            trivy_data = json.loads(trivy_report.data)
            vulnerabilities = trivy_data.get('vulnerabilities', [])
            
            for vuln in vulnerabilities:
                severity = vuln.get('severity', '').lower()
                if severity == 'critical':
                    counts['critical'] += 1
                elif severity == 'high':
                    counts['high'] += 1
                elif severity == 'medium':
                    counts['medium'] += 1
                elif severity == 'low':
                    counts['low'] += 1
        except:
            pass
    
    return counts

def calculate_risk_trend(project):
    """Calculate risk trend for a project"""
    # For now, return neutral trend
    # In a real implementation, this would analyze historical data
    return 'stable'

def calculate_overall_trend_score(projects):
    """Calculate overall trend score across all projects"""
    if not projects:
        return 0
    
    total_risk = 0
    for project in projects:
        risks = project.get('risks', {})
        project_risk = sum(risks.values()) / len(risks) if risks else 0
        total_risk += project_risk
    
    return round(total_risk / len(projects), 1)

def extract_vulnerability_details(trivy_data):
    """Extract detailed vulnerability information"""
    vulnerabilities = trivy_data.get('vulnerabilities', [])
    return [
        {
            'id': v.get('vulnerability_id', 'Unknown'),
            'severity': v.get('severity', 'Unknown'),
            'title': v.get('title', 'No title'),
            'description': v.get('description', 'No description')[:200],
            'package': v.get('package_name', 'Unknown')
        }
        for v in vulnerabilities[:10]  # Limit to first 10
    ]

def get_vulnerability_recommendations(trivy_data):
    """Get vulnerability remediation recommendations"""
    return [
        "Update vulnerable packages to latest versions",
        "Apply security patches from vendors",
        "Review and update container base images",
        "Implement automated vulnerability scanning"
    ]

def extract_code_quality_details(sonar_data):
    """Extract code quality issue details"""
    issues = sonar_data.get('issues', [])
    return [
        {
            'rule': issue.get('rule', 'Unknown'),
            'severity': issue.get('severity', 'Unknown'),
            'message': issue.get('message', 'No message'),
            'component': issue.get('component', 'Unknown')
        }
        for issue in issues[:10]  # Limit to first 10
    ]

def get_code_quality_recommendations(sonar_data):
    """Get code quality improvement recommendations"""
    return [
        "Address critical bugs and vulnerabilities first",
        "Improve test coverage to at least 80%",
        "Reduce code complexity and duplication",
        "Follow established coding standards"
    ]

def extract_dependency_details(sbom_data):
    """Extract dependency risk details"""
    components = sbom_data.get('components', [])
    return [
        {
            'name': comp.get('name', 'Unknown'),
            'version': comp.get('version', 'Unknown'),
            'type': comp.get('type', 'Unknown'),
            'vulnerabilities': len(comp.get('vulnerabilities', []))
        }
        for comp in components[:10]  # Limit to first 10
    ]

def get_dependency_recommendations(sbom_data):
    """Get dependency security recommendations"""
    return [
        "Update outdated dependencies regularly",
        "Monitor for new vulnerability disclosures",
        "Use dependency scanning tools in CI/CD",
        "Maintain an accurate software bill of materials"
    ]

def extract_container_details(trivy_data):
    """Extract container security details"""
    misconfigs = trivy_data.get('misconfigurations', [])
    secrets = trivy_data.get('secrets', [])
    
    details = []
    for config in misconfigs[:5]:
        details.append({
            'type': 'Misconfiguration',
            'rule': config.get('rule', 'Unknown'),
            'severity': config.get('severity', 'Unknown'),
            'message': config.get('message', 'No message')
        })
    
    for secret in secrets[:5]:
        details.append({
            'type': 'Secret',
            'rule': secret.get('rule', 'Unknown'),
            'severity': 'HIGH',
            'message': f"Exposed secret: {secret.get('type', 'Unknown')}"
        })
    
    return details

def get_container_recommendations(trivy_data):
    """Get container security recommendations"""
    return [
        "Use minimal base images with fewer vulnerabilities",
        "Scan images before deployment",
        "Implement proper secret management",
        "Follow container security best practices"
    ]

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
