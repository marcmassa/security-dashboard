import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from utils.parsers import parse_sonarqube_report, parse_sbom_report, parse_trivy_report

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json', 'xml'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for processed reports
reports_data = {
    'sonarqube': None,
    'sbom': None,
    'trivy': None
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', reports_data=reports_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    report_type = request.form.get('report_type')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not report_type or report_type not in ['sonarqube', 'sbom', 'trivy']:
        return jsonify({'error': 'Invalid report type'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Parse the file based on report type
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            if report_type == 'sonarqube':
                parsed_data = parse_sonarqube_report(file_content)
            elif report_type == 'sbom':
                parsed_data = parse_sbom_report(file_content)
            elif report_type == 'trivy':
                parsed_data = parse_trivy_report(file_content)
            
            # Store parsed data in memory
            reports_data[report_type] = parsed_data
            
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
    
    return jsonify({'error': 'Invalid file format. Please upload JSON or XML files.'}), 400

@app.route('/api/summary')
def get_summary():
    """Get summary data for the dashboard"""
    summary = {
        'sonarqube': reports_data.get('sonarqube'),
        'sbom': reports_data.get('sbom'),
        'trivy': reports_data.get('trivy'),
        'total_reports': sum(1 for report in reports_data.values() if report is not None)
    }
    return jsonify(summary)

@app.route('/sonarqube')
def sonarqube_detail():
    if not reports_data.get('sonarqube'):
        flash('No SonarQube report data available. Please upload a report first.', 'warning')
        return redirect(url_for('index'))
    return render_template('sonarqube_detail.html', data=reports_data['sonarqube'])

@app.route('/sbom')
def sbom_detail():
    if not reports_data.get('sbom'):
        flash('No SBOM report data available. Please upload a report first.', 'warning')
        return redirect(url_for('index'))
    return render_template('sbom_detail.html', data=reports_data['sbom'])

@app.route('/trivy')
def trivy_detail():
    if not reports_data.get('trivy'):
        flash('No Trivy report data available. Please upload a report first.', 'warning')
        return redirect(url_for('index'))
    return render_template('trivy_detail.html', data=reports_data['trivy'])

@app.route('/clear')
def clear_data():
    """Clear all stored report data"""
    global reports_data
    reports_data = {
        'sonarqube': None,
        'sbom': None,
        'trivy': None
    }
    flash('All report data cleared successfully.', 'success')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
