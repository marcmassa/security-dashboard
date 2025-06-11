# Security Dashboard v1.0.0

A comprehensive security analysis platform that aggregates and visualizes security reports from multiple sources, providing real-time insights and actionable intelligence for development teams.

## ✨ Features

### Core Capabilities
- **Multi-Source Security Analysis**: Integrates SonarQube, SBOM (CycloneDX), and Trivy reports
- **Interactive Security Risk Heatmap**: Real-time threat visualization with multiple view modes
- **Progressive Information Display**: Shows data as reports are uploaded
- **Comprehensive Dashboards**: Summary views and detailed analysis for each report type
- **Real-time Monitoring**: Live updates and security threat notifications
- **Export Capabilities**: PDF and JSON export options with detailed reporting

### Security Features
- **Vulnerability Assessment**: Multi-source vulnerability aggregation and analysis
- **Code Quality Metrics**: SonarQube integration with trend analysis
- **Dependency Analysis**: SBOM parsing with outdated package detection
- **Container Security**: Trivy integration for container vulnerability scanning
- **Risk Scoring**: Intelligent risk calculation across four security categories
- **Threat Intelligence**: AI-powered insights and recommendations

### Enterprise Features
- **Role-based Access Control**: Admin and user permission levels
- **SSO/SAML Integration**: Enterprise authentication support
- **CI/CD Integration**: Jenkins integration scripts and webhook support
- **Kubernetes Deployment**: Production-ready containerized deployment
- **API-First Design**: RESTful APIs for external integrations

## 🛠 Technology Stack

- **Backend**: Flask (Python 3.11+)
- **Frontend**: Bootstrap 5 + Modern JavaScript
- **Database**: PostgreSQL with optimized queries
- **Visualization**: Chart.js, Canvas-based interactive charts
- **Deployment**: Kubernetes (GKE) with Docker
- **Authentication**: Flask-Login with SSO/SAML support
- **Security**: JWT tokens, secure session management

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- SonarQube server (optional but recommended)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd security-dashboard

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export DATABASE_URL="postgresql://user:pass@localhost/securitydb"
export SESSION_SECRET="your-secure-secret-key"

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Run the application
python main.py
```

### First Time Setup
1. Access the application at `http://localhost:5000`
2. Navigate to Configuration (Admin access required)
3. Configure SonarQube integration if available
4. Create your first project
5. Upload security reports to start analysis

## 📊 Security Risk Heatmap

The interactive security heatmap provides comprehensive threat visualization:

### View Modes
- **Grid View**: Matrix display of risk scores across projects and categories
- **Tree Map**: Hierarchical visualization showing risk distribution
- **Bubble Chart**: Interactive bubbles sized by risk severity

### Risk Categories
- **Vulnerabilities**: CVE analysis from Trivy and SBOM data
- **Code Quality**: SonarQube metrics including bugs and code smells
- **Dependencies**: Outdated packages and vulnerable dependencies
- **Containers**: Container-specific security issues and misconfigurations

### Real-time Features
- Automatic data refresh (configurable intervals)
- Live threat monitoring and notifications
- Timeline visualization showing 24-hour risk trends
- Interactive drill-down for detailed risk analysis

## ⚙️ Configuration

### SonarQube Integration
1. Navigate to **Configuration → SonarQube Integration**
2. Enter your SonarQube server URL and authentication token
3. Test connection and save configuration
4. Projects can now fetch data directly from SonarQube

### Project Management
1. Create projects through the **New Project** button
2. Upload reports individually or via CI/CD integration
3. View real-time analysis as reports are processed
4. Access the Security Heatmap for cross-project risk visualization

## 🔄 CI/CD Integration

### Jenkins Pipeline Integration
```bash
python scripts/jenkins-integration.py \
  --dashboard-url "https://security-dashboard.company.com" \
  --project "MyProject" \
  --sonarqube-report "reports/sonar-report.json" \
  --sbom-report "reports/sbom.json" \
  --trivy-report "reports/trivy-report.json" \
  --jenkins-build "${BUILD_NUMBER}" \
  --jenkins-url "${BUILD_URL}"
```

### Webhook Notifications
Configure external systems to receive security updates:
```bash
curl -X POST "https://security-dashboard.company.com/api/projects/{id}/webhook" \
  -H "Content-Type: application/json" \
  -d '{"event": "scan_complete", "severity": "high", "details": "..."}'
```

## 🐳 Deployment

### Production Deployment (Kubernetes)
```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=security-dashboard

# Access via LoadBalancer
kubectl get services security-dashboard-service
```

### Development Deployment (Docker)
```bash
# Build container
docker build -t security-dashboard:1.0.0 .

# Run with database
docker-compose up -d

# Access at http://localhost:5000
```

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost/securitydb
SESSION_SECRET=your-256-bit-secret-key
SONAR_URL=https://sonarqube.company.com
FLASK_ENV=production
GUNICORN_WORKERS=4
```

## 📈 API Documentation

### Core Endpoints
```bash
# Project Management
POST   /projects                    # Create new project
GET    /projects/{id}              # Get project details
DELETE /projects/{id}              # Delete project

# Report Upload
POST   /projects/{id}/upload       # Upload security reports
GET    /projects/{id}/summary      # Get aggregated summary

# Detailed Analysis
GET    /projects/{id}/sonarqube    # SonarQube analysis
GET    /projects/{id}/sbom         # SBOM dependency analysis  
GET    /projects/{id}/trivy        # Trivy security scan

# Security Heatmap
GET    /api/security-heatmap/data  # Heatmap visualization data
GET    /api/security-heatmap/timeline # Historical risk data
GET    /api/security-heatmap/details/{project}/{category} # Detailed risk info

# External Integration
POST   /api/projects/find-or-create # Jenkins integration
POST   /api/projects/{id}/webhook   # Webhook notifications
GET    /api/projects/{id}/status    # Project status for CI/CD
```

### Authentication
All API endpoints support both session-based and token-based authentication.

## 🔒 Security & Compliance

### Data Security
- All sensitive data encrypted at rest and in transit
- Secure session management with httpOnly cookies
- CSRF protection on all state-changing operations
- SQL injection prevention through parameterized queries

### Access Control
- Role-based permissions (Admin/User)
- Project-level access restrictions
- Audit logging for security events
- SSO/SAML integration for enterprise environments

### Compliance Features
- Vulnerability tracking and remediation workflows
- Compliance reporting with historical trends
- Risk assessment scoring and prioritization
- Integration with ticketing systems for issue tracking

## 🧪 Testing & Quality

### Report Format Support
- **SonarQube**: JSON format from SonarQube API or exported reports
- **SBOM**: CycloneDX format (JSON/XML) with component vulnerability data
- **Trivy**: JSON format including vulnerabilities, secrets, and misconfigurations

### Validation
All uploaded reports are validated for:
- Correct JSON/XML format
- Required fields and data structure
- Security scan completeness
- Timestamp and versioning information

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black app.py models.py
flake8 --max-line-length=88

# Pre-commit hooks
pre-commit install
```

### Pull Request Process
1. Fork the repository and create a feature branch
2. Implement changes with comprehensive tests
3. Ensure all security checks pass
4. Update documentation as needed
5. Submit pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: Create detailed bug reports and feature requests
- **Discussions**: Community support and questions
- **Security**: Report vulnerabilities through responsible disclosure
- **Enterprise**: Contact team for enterprise support and customization

### Version History
- **v1.0.0** (Current): Initial production release with security heatmap
- **v0.9.x**: Beta releases with core functionality
- **v0.8.x**: Alpha releases with basic report processing

---

**Security Dashboard v1.0.0** - Comprehensive security analysis platform for modern development teams.