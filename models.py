from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import json


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sonar_project_key = db.Column(db.String(255), nullable=True)  # SonarQube project key
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reports': {
                'sonarqube': self.get_report('sonarqube'),
                'sbom': self.get_report('sbom'),
                'trivy': self.get_report('trivy')
            }
        }
    
    def get_report(self, report_type):
        report = Report.query.filter_by(project_id=self.id, report_type=report_type).first()
        return json.loads(report.data) if report and report.data else None
    
    def set_report(self, report_type, data):
        report = Report.query.filter_by(project_id=self.id, report_type=report_type).first()
        if report:
            report.data = json.dumps(data)
            report.updated_at = datetime.utcnow()
        else:
            report = Report(
                project_id=self.id,
                report_type=report_type,
                data=json.dumps(data)
            )
            db.session.add(report)
        db.session.commit()


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # 'sonarqube', 'sbom', 'trivy'
    data = db.Column(db.Text)  # JSON data as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to ensure one report per type per project
    __table_args__ = (db.UniqueConstraint('project_id', 'report_type', name='_project_report_type_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'report_type': self.report_type,
            'data': json.loads(self.data) if self.data else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }