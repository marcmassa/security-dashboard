import json
import xml.etree.ElementTree as ET
import logging
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

def parse_sonarqube_report(content: str) -> Dict[str, Any]:
    """Parse SonarQube JSON report"""
    try:
        data = json.loads(content)
        
        # Extract metrics from SonarQube report
        measures = data.get('component', {}).get('measures', [])
        metrics = {}
        
        for measure in measures:
            metric_key = measure.get('metric')
            metric_value = measure.get('value', '0')
            metrics[metric_key] = metric_value
        
        # Parse key metrics
        parsed_data = {
            'project_key': data.get('component', {}).get('key', 'Unknown'),
            'project_name': data.get('component', {}).get('name', 'Unknown'),
            'bugs': int(metrics.get('bugs', 0)),
            'vulnerabilities': int(metrics.get('vulnerabilities', 0)),
            'code_smells': int(metrics.get('code_smells', 0)),
            'coverage': float(metrics.get('coverage', 0.0)),
            'duplicated_lines_density': float(metrics.get('duplicated_lines_density', 0.0)),
            'lines': int(metrics.get('lines', 0)),
            'ncloc': int(metrics.get('ncloc', 0)),
            'complexity': int(metrics.get('complexity', 0)),
            'security_hotspots': int(metrics.get('security_hotspots', 0)),
            'sqale_rating': metrics.get('sqale_rating', 'A'),
            'reliability_rating': metrics.get('reliability_rating', 'A'),
            'security_rating': metrics.get('security_rating', 'A'),
            'raw_data': data
        }
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in SonarQube report: {e}")
        raise ValueError("Invalid JSON format in SonarQube report")
    except Exception as e:
        logging.error(f"Error parsing SonarQube report: {e}")
        raise ValueError(f"Error parsing SonarQube report: {e}")

def parse_sbom_report(content: str) -> Dict[str, Any]:
    """Parse SBOM CycloneDX report (JSON or XML)"""
    try:
        # Try JSON first
        try:
            data = json.loads(content)
            return _parse_sbom_json(data)
        except json.JSONDecodeError:
            # Try XML
            return _parse_sbom_xml(content)
            
    except Exception as e:
        logging.error(f"Error parsing SBOM report: {e}")
        raise ValueError(f"Error parsing SBOM report: {e}")

def _parse_sbom_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON format SBOM"""
    components = data.get('components', [])
    vulnerabilities = data.get('vulnerabilities', [])
    
    # Count vulnerabilities by severity
    severity_counts = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'info': 0,
        'unknown': 0
    }
    
    # Process vulnerabilities
    for vuln in vulnerabilities:
        ratings = vuln.get('ratings', [])
        if ratings:
            severity = ratings[0].get('severity', 'unknown').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts['unknown'] += 1
    
    # Process components
    component_summary = {
        'total': len(components),
        'by_type': {},
        'licenses': set()
    }
    
    for component in components:
        comp_type = component.get('type', 'unknown')
        component_summary['by_type'][comp_type] = component_summary['by_type'].get(comp_type, 0) + 1
        
        # Extract licenses
        licenses = component.get('licenses', [])
        for license_info in licenses:
            if 'license' in license_info:
                license_name = license_info['license'].get('name') or license_info['license'].get('id')
                if license_name:
                    component_summary['licenses'].add(license_name)
    
    component_summary['licenses'] = list(component_summary['licenses'])
    
    return {
        'bom_format': data.get('bomFormat', 'CycloneDX'),
        'spec_version': data.get('specVersion', 'Unknown'),
        'metadata': data.get('metadata', {}),
        'components': component_summary,
        'vulnerabilities': {
            'total': len(vulnerabilities),
            'by_severity': severity_counts
        },
        'raw_data': data
    }

def _parse_sbom_xml(content: str) -> Dict[str, Any]:
    """Parse XML format SBOM"""
    try:
        root = ET.fromstring(content)
        
        # Handle namespaces
        ns = {'bom': 'http://cyclonedx.org/schema/bom/1.4'}
        if root.tag.startswith('{'):
            # Extract namespace from root tag
            ns_uri = root.tag.split('}')[0][1:]
            ns = {'bom': ns_uri}
        
        # Get basic info
        bom_format = 'CycloneDX'
        spec_version = root.get('version', 'Unknown')
        
        # Count components
        components = root.findall('.//bom:component', ns) or root.findall('.//component')
        component_summary = {
            'total': len(components),
            'by_type': {},
            'licenses': set()
        }
        
        for component in components:
            comp_type = component.get('type', 'unknown')
            component_summary['by_type'][comp_type] = component_summary['by_type'].get(comp_type, 0) + 1
        
        component_summary['licenses'] = list(component_summary['licenses'])
        
        # For XML, vulnerability parsing is more complex and varies by schema version
        # For now, return basic structure
        return {
            'bom_format': bom_format,
            'spec_version': spec_version,
            'metadata': {},
            'components': component_summary,
            'vulnerabilities': {
                'total': 0,
                'by_severity': {
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0,
                    'info': 0,
                    'unknown': 0
                }
            },
            'raw_data': content
        }
        
    except ET.ParseError as e:
        logging.error(f"Invalid XML in SBOM report: {e}")
        raise ValueError("Invalid XML format in SBOM report")

def parse_trivy_report(content: str) -> Dict[str, Any]:
    """Parse Trivy JSON report"""
    try:
        data = json.loads(content)
        
        # Initialize counters
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'UNKNOWN': 0
        }
        
        total_vulnerabilities = 0
        results = data.get('Results', [])
        
        # Process each result
        for result in results:
            vulnerabilities = result.get('Vulnerabilities', [])
            for vuln in vulnerabilities:
                severity = vuln.get('Severity', 'UNKNOWN').upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
                else:
                    severity_counts['UNKNOWN'] += 1
                total_vulnerabilities += 1
        
        # Extract metadata
        artifact_name = data.get('ArtifactName', 'Unknown')
        artifact_type = data.get('ArtifactType', 'Unknown')
        
        return {
            'artifact_name': artifact_name,
            'artifact_type': artifact_type,
            'schema_version': data.get('SchemaVersion', 'Unknown'),
            'vulnerabilities': {
                'total': total_vulnerabilities,
                'by_severity': severity_counts
            },
            'results': results,
            'raw_data': data
        }
        
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in Trivy report: {e}")
        raise ValueError("Invalid JSON format in Trivy report")
    except Exception as e:
        logging.error(f"Error parsing Trivy report: {e}")
        raise ValueError(f"Error parsing Trivy report: {e}")

def parse_trivy_html_report(content: str) -> Dict[str, Any]:
    """Parse Trivy HTML report"""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Initialize counters
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'UNKNOWN': 0
        }
        
        # Extract artifact name from title or h1
        artifact_name = 'Unknown'
        title = soup.find('title')
        if title:
            artifact_name = title.get_text().strip()
        elif soup.find('h1'):
            artifact_name = soup.find('h1').get_text().strip()
        
        # Try to extract vulnerability information from tables
        results = []
        total_vulnerabilities = 0
        
        # Look for vulnerability tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 4:  # Minimum expected columns
                    vulnerability = {}
                    
                    # Try to extract CVE ID
                    if cells[0].get_text().strip().startswith('CVE-'):
                        vulnerability['VulnerabilityID'] = cells[0].get_text().strip()
                    
                    # Try to extract package name
                    if len(cells) > 1:
                        vulnerability['PkgName'] = cells[1].get_text().strip()
                    
                    # Try to extract severity
                    severity_cell = None
                    for cell in cells:
                        cell_text = cell.get_text().strip().upper()
                        if cell_text in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
                            severity_cell = cell_text
                            break
                    
                    if severity_cell:
                        vulnerability['Severity'] = severity_cell
                        severity_counts[severity_cell] += 1
                        total_vulnerabilities += 1
                    
                    # Try to extract other fields
                    if len(cells) > 2:
                        vulnerability['InstalledVersion'] = cells[2].get_text().strip()
                    if len(cells) > 3:
                        vulnerability['Title'] = cells[3].get_text().strip()
                    
                    if vulnerability:
                        # Create a result structure similar to JSON format
                        if not results:
                            results.append({
                                'Target': artifact_name,
                                'Type': 'container',
                                'Vulnerabilities': []
                            })
                        
                        results[0]['Vulnerabilities'].append(vulnerability)
        
        # If no structured data found, try to extract summary information
        if total_vulnerabilities == 0:
            # Look for severity badges or spans
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                elements = soup.find_all(text=re.compile(severity, re.IGNORECASE))
                for element in elements:
                    # Try to extract numbers near severity keywords
                    parent = element.parent if hasattr(element, 'parent') else None
                    if parent:
                        numbers = re.findall(r'\d+', parent.get_text())
                        if numbers:
                            count = int(numbers[0])
                            severity_counts[severity] += count
                            total_vulnerabilities += count
        
        return {
            'artifact_name': artifact_name,
            'artifact_type': 'container',
            'schema_version': 'HTML',
            'vulnerabilities': {
                'total': total_vulnerabilities,
                'by_severity': severity_counts
            },
            'results': results,
            'raw_data': {'html_content': content}
        }
        
    except Exception as e:
        logging.error(f"Error parsing Trivy HTML report: {e}")
        raise ValueError(f"Error parsing Trivy HTML report: {e}")
