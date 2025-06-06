#!/usr/bin/env python3
"""
SonarQube API Client for Security Dashboard
Fetches project metrics and issues directly from SonarQube server
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64

class SonarQubeClient:
    def __init__(self, base_url: str, token: str):
        """Initialize SonarQube client
        
        Args:
            base_url: SonarQube server URL (e.g., https://sonarqube.company.com)
            token: SonarQube authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Setup authentication
        auth_string = f"{token}:"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        })
    
    def get_project_measures(self, project_key: str) -> Dict[str, Any]:
        """Get project metrics from SonarQube API
        
        Args:
            project_key: SonarQube project key
            
        Returns:
            Dictionary with parsed project metrics
        """
        try:
            # Define metrics to fetch
            metrics = [
                'bugs', 'vulnerabilities', 'code_smells', 'security_hotspots',
                'coverage', 'duplicated_lines_density', 'lines', 'ncloc',
                'complexity', 'sqale_rating', 'reliability_rating', 'security_rating',
                'alert_status', 'sqale_index',
                'new_bugs', 'new_vulnerabilities', 'new_code_smells'
            ]
            
            url = f"{self.base_url}/api/measures/component"
            params = {
                'component': project_key,
                'metricKeys': ','.join(metrics)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            # Handle specific HTTP errors with detailed messages
            if response.status_code == 403:
                raise Exception(f"Access denied to SonarQube project '{project_key}'. Please verify:\n"
                              f"• Your token has 'Browse' permission for this project\n"
                              f"• The project key '{project_key}' is correct\n"
                              f"• Your token is valid and not expired")
            elif response.status_code == 404:
                raise Exception(f"Project '{project_key}' not found in SonarQube. Please check the project key.")
            elif response.status_code == 401:
                raise Exception("Authentication failed. Please verify your SonarQube token is correct.")
            
            response.raise_for_status()
            
            data = response.json()
            component = data.get('component', {})
            measures = component.get('measures', [])
            
            # Parse measures into structured format
            metrics_dict = {}
            for measure in measures:
                metric_key = measure.get('metric')
                metric_value = measure.get('value', '0')
                metrics_dict[metric_key] = metric_value
            
            # Get project info
            project_info = self._get_project_info(project_key)
            
            return {
                'project_key': component.get('key', project_key),
                'project_name': component.get('name', project_info.get('name', 'Unknown')),
                'project_description': project_info.get('description', ''),
                'last_analysis': project_info.get('lastAnalysisDate'),
                'bugs': int(metrics_dict.get('bugs', 0)),
                'vulnerabilities': int(metrics_dict.get('vulnerabilities', 0)),
                'code_smells': int(metrics_dict.get('code_smells', 0)),
                'security_hotspots': int(metrics_dict.get('security_hotspots', 0)),
                'coverage': float(metrics_dict.get('coverage', 0.0)),
                'duplicated_lines_density': float(metrics_dict.get('duplicated_lines_density', 0.0)),
                'lines': int(metrics_dict.get('lines', 0)),
                'ncloc': int(metrics_dict.get('ncloc', 0)),
                'complexity': int(metrics_dict.get('complexity', 0)),
                'sqale_rating': metrics_dict.get('sqale_rating', 'A'),
                'reliability_rating': metrics_dict.get('reliability_rating', 'A'),
                'security_rating': metrics_dict.get('security_rating', 'A'),
                'quality_gate_status': metrics_dict.get('quality_gate_status', 'OK'),
                'technical_debt': metrics_dict.get('technical_debt', '0min'),
                'new_bugs': int(metrics_dict.get('new_bugs', 0)),
                'new_vulnerabilities': int(metrics_dict.get('new_vulnerabilities', 0)),
                'new_code_smells': int(metrics_dict.get('new_code_smells', 0)),
                'raw_metrics': metrics_dict
            }
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching SonarQube metrics: {e}")
            raise Exception(f"Failed to fetch SonarQube metrics: {e}")
    
    def get_project_issues(self, project_key: str, issue_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get project issues from SonarQube API
        
        Args:
            project_key: SonarQube project key
            issue_types: List of issue types (BUG, VULNERABILITY, CODE_SMELL)
            
        Returns:
            List of issues with details
        """
        try:
            if issue_types is None:
                issue_types = ['BUG', 'VULNERABILITY', 'CODE_SMELL']
            
            url = f"{self.base_url}/api/issues/search"
            params = {
                'componentKeys': project_key,
                'types': ','.join(issue_types),
                'ps': 500,  # Page size
                'facets': 'types,severities,statuses'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            
            # Parse issues
            parsed_issues = []
            for issue in issues:
                parsed_issue = {
                    'key': issue.get('key'),
                    'rule': issue.get('rule'),
                    'severity': issue.get('severity'),
                    'component': issue.get('component'),
                    'project': issue.get('project'),
                    'line': issue.get('line'),
                    'message': issue.get('message'),
                    'author': issue.get('author'),
                    'creation_date': issue.get('creationDate'),
                    'update_date': issue.get('updateDate'),
                    'type': issue.get('type'),
                    'status': issue.get('status'),
                    'effort': issue.get('effort'),
                    'tags': issue.get('tags', [])
                }
                parsed_issues.append(parsed_issue)
            
            return parsed_issues
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching SonarQube issues: {e}")
            raise Exception(f"Failed to fetch SonarQube issues: {e}")
    
    def get_security_hotspots(self, project_key: str) -> List[Dict[str, Any]]:
        """Get security hotspots from SonarQube API
        
        Args:
            project_key: SonarQube project key
            
        Returns:
            List of security hotspots with details
        """
        try:
            url = f"{self.base_url}/api/hotspots/search"
            params = {
                'projectKey': project_key,
                'ps': 500
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            hotspots = data.get('hotspots', [])
            
            # Parse hotspots
            parsed_hotspots = []
            for hotspot in hotspots:
                parsed_hotspot = {
                    'key': hotspot.get('key'),
                    'component': hotspot.get('component'),
                    'project': hotspot.get('project'),
                    'rule': hotspot.get('rule'),
                    'status': hotspot.get('status'),
                    'line': hotspot.get('line'),
                    'message': hotspot.get('message'),
                    'author': hotspot.get('author'),
                    'creation_date': hotspot.get('creationDate'),
                    'update_date': hotspot.get('updateDate'),
                    'vulnerability_probability': hotspot.get('vulnerabilityProbability')
                }
                parsed_hotspots.append(parsed_hotspot)
            
            return parsed_hotspots
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching SonarQube hotspots: {e}")
            raise Exception(f"Failed to fetch SonarQube hotspots: {e}")
    
    def _get_project_info(self, project_key: str) -> Dict[str, Any]:
        """Get basic project information
        
        Args:
            project_key: SonarQube project key
            
        Returns:
            Dictionary with project information
        """
        try:
            url = f"{self.base_url}/api/projects/search"
            params = {
                'projects': project_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            components = data.get('components', [])
            
            if components:
                return components[0]
            else:
                return {}
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Could not fetch project info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test connection to SonarQube server
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/system/status"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('status') == 'UP'
            
        except Exception as e:
            logging.error(f"SonarQube connection test failed: {e}")
            return False


def fetch_sonarqube_data(base_url: str, token: str, project_key: str) -> Dict[str, Any]:
    """Main function to fetch comprehensive SonarQube data
    
    Args:
        base_url: SonarQube server URL
        token: Authentication token
        project_key: Project key to analyze
        
    Returns:
        Comprehensive project data dictionary
    """
    client = SonarQubeClient(base_url, token)
    
    # Test connection first
    if not client.test_connection():
        raise Exception("Cannot connect to SonarQube server")
    
    # Fetch all data
    measures = client.get_project_measures(project_key)
    issues = client.get_project_issues(project_key)
    hotspots = client.get_security_hotspots(project_key)
    
    # Combine into comprehensive report
    return {
        **measures,
        'issues': issues,
        'issues_count': len(issues),
        'security_hotspots_list': hotspots,
        'hotspots_count': len(hotspots),
        'fetch_timestamp': datetime.utcnow().isoformat()
    }


if __name__ == '__main__':
    # Example usage
    import os
    
    base_url = os.environ.get('SONAR_HOST_URL', 'https://sonarqube.example.com')
    token = os.environ.get('SONAR_TOKEN')
    project_key = os.environ.get('SONAR_PROJECT_KEY')
    
    if not all([base_url, token, project_key]):
        print("Please set SONAR_HOST_URL, SONAR_TOKEN, and SONAR_PROJECT_KEY environment variables")
        exit(1)
    
    try:
        data = fetch_sonarqube_data(base_url, token, project_key)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)