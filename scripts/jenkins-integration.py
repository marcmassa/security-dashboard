#!/usr/bin/env python3
"""
Security Dashboard Jenkins Integration Script
Uploads security reports to the dashboard from Jenkins CI/CD pipeline
"""

import requests
import argparse
import sys
import os
import json
from typing import Optional, Dict, Any

class SecurityDashboardClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def find_or_create_project(self, name: str) -> str:
        """Find existing project by name or create new one"""
        try:
            response = self.session.post(
                f'{self.base_url}/api/projects/find-or-create',
                json={'name': name},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('created'):
                print(f"Created new project: {name}")
            else:
                print(f"Found existing project: {name}")
            
            return data['project_id']
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to find/create project: {e}")
    
    def upload_report(self, project_id: str, report_type: str, file_path: str) -> Dict[str, Any]:
        """Upload a security report to the project"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Report file not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'report_type': report_type}
                
                response = self.session.post(
                    f'{self.base_url}/project/{project_id}/upload',
                    files=files,
                    data=data,
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to upload {report_type} report: {e}")
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current project status"""
        try:
            response = self.session.get(
                f'{self.base_url}/api/projects/{project_id}/status',
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get project status: {e}")
    
    def send_webhook(self, project_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            response = self.session.post(
                f'{self.base_url}/api/projects/{project_id}/webhook',
                json=event_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send webhook: {e}")

def validate_report_file(file_path: str, report_type: str) -> bool:
    """Validate report file format"""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            
        if report_type in ['sonarqube', 'trivy'] and file_path.endswith('.json'):
            json.loads(content)  # Validate JSON
            return True
        elif report_type == 'sbom' and (file_path.endswith('.json') or file_path.endswith('.xml')):
            if file_path.endswith('.json'):
                json.loads(content)  # Validate JSON
            return True
        elif report_type == 'trivy' and file_path.endswith('.html'):
            return '<html' in content.lower()
        
        return False
        
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

def upload_reports(dashboard_url: str, project_name: str, reports: Dict[str, str], 
                  jenkins_build: Optional[str] = None, jenkins_url: Optional[str] = None) -> None:
    """Main function to upload reports to dashboard"""
    
    print(f"Connecting to Security Dashboard: {dashboard_url}")
    client = SecurityDashboardClient(dashboard_url)
    
    try:
        # Find or create project
        project_id = client.find_or_create_project(project_name)
        print(f"Using project ID: {project_id}")
        
        # Upload each report
        uploaded_reports = []
        for report_type, file_path in reports.items():
            if not os.path.exists(file_path):
                print(f"⚠ Warning: {report_type} report not found: {file_path}")
                continue
            
            # Validate report format
            if not validate_report_file(file_path, report_type):
                print(f"⚠ Warning: Invalid {report_type} report format: {file_path}")
                continue
            
            try:
                result = client.upload_report(project_id, report_type, file_path)
                
                if result.get('success'):
                    print(f"✓ {report_type.upper()} report uploaded successfully")
                    uploaded_reports.append(report_type)
                else:
                    print(f"✗ Failed to upload {report_type}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"✗ Error uploading {report_type}: {e}")
        
        # Send webhook notification if Jenkins info is available
        if jenkins_build and jenkins_url and uploaded_reports:
            webhook_data = {
                'event': 'scan_completed',
                'build_number': jenkins_build,
                'jenkins_url': jenkins_url,
                'reports_uploaded': uploaded_reports,
                'project_name': project_name
            }
            
            try:
                client.send_webhook(project_id, webhook_data)
                print(f"✓ Webhook notification sent")
            except Exception as e:
                print(f"⚠ Warning: Failed to send webhook: {e}")
        
        # Get final project status
        try:
            status = client.get_project_status(project_id)
            total_reports = status.get('total_reports', 0)
            print(f"\nProject Status: {total_reports} reports uploaded")
            
            for report_type, report_status in status.get('reports_status', {}).items():
                if report_status.get('uploaded'):
                    print(f"  ✓ {report_type.upper()}: uploaded")
                else:
                    print(f"  ○ {report_type.upper()}: not uploaded")
                    
        except Exception as e:
            print(f"⚠ Warning: Could not retrieve project status: {e}")
        
        # Print dashboard URL
        print(f"\n🔗 Dashboard URL: {dashboard_url}/project/{project_id}")
        
        if not uploaded_reports:
            print("\n⚠ No reports were uploaded successfully")
            sys.exit(1)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Upload security reports to Security Dashboard from Jenkins'
    )
    
    # Required arguments
    parser.add_argument('--dashboard-url', required=True,
                       help='Security Dashboard URL (e.g., https://dashboard.example.com)')
    parser.add_argument('--project-name', required=True,
                       help='Project name (usually Jenkins job name)')
    
    # Report file arguments
    parser.add_argument('--sonarqube-report',
                       help='Path to SonarQube JSON report')
    parser.add_argument('--sbom-report',
                       help='Path to SBOM CycloneDX report (JSON or XML)')
    parser.add_argument('--trivy-report',
                       help='Path to Trivy report (JSON or HTML)')
    
    # Jenkins integration arguments
    parser.add_argument('--jenkins-build',
                       help='Jenkins build number (e.g., $BUILD_NUMBER)')
    parser.add_argument('--jenkins-url',
                       help='Jenkins build URL (e.g., $BUILD_URL)')
    
    # Optional arguments
    parser.add_argument('--api-key',
                       help='API key for authentication (if required)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Collect reports to upload
    reports = {}
    if args.sonarqube_report:
        reports['sonarqube'] = args.sonarqube_report
    if args.sbom_report:
        reports['sbom'] = args.sbom_report
    if args.trivy_report:
        reports['trivy'] = args.trivy_report
    
    if not reports:
        print("Error: At least one report file must be specified")
        sys.exit(1)
    
    # Set verbose mode
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Upload reports
    upload_reports(
        dashboard_url=args.dashboard_url,
        project_name=args.project_name,
        reports=reports,
        jenkins_build=args.jenkins_build,
        jenkins_url=args.jenkins_url
    )

if __name__ == '__main__':
    main()