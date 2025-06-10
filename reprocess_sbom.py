#!/usr/bin/env python3
"""
Script to reprocess existing SBOM data with improved parser
"""

import json
from app import app, db
from models import Report
from utils.parsers import parse_sbom_report

def reprocess_sbom_reports():
    """Reprocess all SBOM reports with improved parser"""
    with app.app_context():
        sbom_reports = Report.query.filter_by(report_type='sbom').all()
        
        for report in sbom_reports:
            try:
                print(f"Reprocessing SBOM report for project {report.project_id}")
                
                # Get the raw XML data
                current_data = json.loads(report.data)
                raw_xml = current_data.get('raw_data', '')
                
                if raw_xml:
                    # Reparse with improved parser
                    new_data = parse_sbom_report(raw_xml)
                    
                    # Update the report
                    report.data = json.dumps(new_data)
                    db.session.commit()
                    
                    print(f"✓ Updated SBOM report - Components: {new_data['components']['total']}")
                    print(f"  - Component types: {list(new_data['components']['by_type'].keys())}")
                    print(f"  - Licenses found: {len(new_data['components']['licenses'])}")
                    print(f"  - Component details: {len(new_data['components'].get('details', []))}")
                else:
                    print(f"✗ No raw data found for report {report.id}")
                    
            except Exception as e:
                print(f"✗ Error reprocessing report {report.id}: {e}")

if __name__ == '__main__':
    reprocess_sbom_reports()