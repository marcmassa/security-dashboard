import os
import json
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from utils.parsers import parse_sonarqube_report, parse_sbom_report, parse_trivy_report, parse_trivy_html_report
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
    projects = Project.query.order_by(Project.created_at.desc()).all()
    projects_dict = {project.id: project.to_dict() for project in projects}
    return render_template('home.html', projects=projects_dict)

@app.route('/create-project', methods=['GET', 'POST'])
def create_project_route():
    """Create a new project"""
    if request.method == 'POST':
        project_name = request.form.get('project_name', '').strip()
        if not project_name:
            flash('Project name is required.', 'error')
            return render_template('create_project.html')
        
        project_id = create_project(project_name)
        flash(f'Project "{project_name}" created successfully.', 'success')
        return redirect(url_for('project_dashboard', project_id=project_id))
    
    return render_template('create_project.html')

@app.route('/project/<project_id>')
def project_dashboard(project_id):
    """Project dashboard page"""
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    return render_template('project_dashboard.html', project=project.to_dict())

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
    if not project_data['reports'].get('sonarqube'):
        flash('No SonarQube report data available. Please upload a report first.', 'warning')
        return redirect(url_for('project_dashboard', project_id=project_id))
    
    return render_template('sonarqube_detail.html', 
                         data=project_data['reports']['sonarqube'], 
                         project=project_data)

@app.route('/project/<project_id>/sbom')
def project_sbom_detail(project_id):
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    project_data = project.to_dict()
    if not project_data['reports'].get('sbom'):
        flash('No SBOM report data available. Please upload a report first.', 'warning')
        return redirect(url_for('project_dashboard', project_id=project_id))
    
    return render_template('sbom_detail.html', 
                         data=project_data['reports']['sbom'], 
                         project=project_data)

@app.route('/project/<project_id>/trivy')
def project_trivy_detail(project_id):
    project = Project.query.get(project_id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('home'))
    
    project_data = project.to_dict()
    if not project_data['reports'].get('trivy'):
        flash('No Trivy report data available. Please upload a report first.', 'warning')
        return redirect(url_for('project_dashboard', project_id=project_id))
    
    return render_template('trivy_detail.html', 
                         data=project_data['reports']['trivy'], 
                         project=project_data)

@app.route('/project/<project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get(project_id)
    if project:
        project_name = project.name
        db.session.delete(project)
        db.session.commit()
        flash(f'Project "{project_name}" deleted successfully.', 'success')
    else:
        flash('Project not found.', 'error')
    
    return redirect(url_for('home'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
