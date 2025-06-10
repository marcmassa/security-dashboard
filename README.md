# Security Analysis Dashboard

Comprehensive security analysis dashboard that aggregates and visualizes security reports from multiple sources, providing real-time insights and actionable intelligence for development teams.

## Features

### Core Functionality
- **Multi-Source Integration**: SonarQube, SBOM (CycloneDX), and Trivy security reports
- **Interactive Dashboards**: Real-time visualization with Chart.js and responsive design
- **Project Management**: Organize security reports by project with comprehensive tracking
- **Advanced Report Analysis**: Detailed breakdown with filtering, sorting, and search
- **File Upload Interface**: Dedicated upload buttons for each report type with validation

### Enhanced Report Processing
- **SonarQube Integration**: 
  - Direct API connectivity to SonarQube servers
  - JSON report parsing with issue categorization
  - Interactive tables with filtering by severity, type, and component
  - Code quality metrics and technical debt visualization
  
- **SBOM Analysis**:
  - CycloneDX JSON and XML format support
  - Component dependency analysis with detailed metadata
  - License detection and compliance tracking
  - Enhanced XML parsing with multi-namespace support
  
- **Trivy Container Scanning**:
  - JSON report processing for container vulnerabilities
  - CVSS scoring integration and CVE linking
  - Package-level vulnerability tracking
  - Resizable table interface with sticky headers

### User Interface Enhancements
- **Professional Design**: Bootstrap-based dark theme with compact layouts
- **Interactive Tables**: Real-time filtering, sorting, and search across all views
- **Responsive Layout**: Mobile-optimized with space-efficient design
- **Export Capabilities**: PDF and JSON export for compliance reporting
- **Upload Management**: Individual upload functionality for each report type

## Technology Stack

- **Backend**: Flask (Python) with SQLAlchemy ORM
- **Database**: PostgreSQL with optimized schema and indexing
- **Frontend**: JavaScript ES6, Bootstrap 5, Chart.js, Feather Icons
- **File Processing**: Multi-format parsers (JSON, XML, HTML)
- **Containerization**: Docker with optimized builds
- **Orchestration**: Kubernetes with health checks and auto-scaling
- **CI/CD**: Jenkins integration with webhook support

## Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Docker (optional)

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd security-dashboard

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/security_dashboard"
export SESSION_SECRET="your-secure-secret-key"

# Run application
python main.py
# Access at http://localhost:5000
```

### Docker Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Access at http://localhost:5000
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f k8s/

# Check services
kubectl get services
```

## Usage Guide

### Project Management

1. **Create Project**: Click "Create New Project" on homepage
2. **Upload Reports**: Use dedicated upload buttons for each report type
3. **View Analysis**: Navigate through interactive dashboards and detailed views
4. **Export Data**: Generate PDF or JSON reports for compliance

### Report Analysis Features

#### SonarQube Reports
- **Upload Format**: JSON from SonarQube API or export
- **Analysis Capabilities**: Code quality metrics, security hotspots, technical debt
- **Interactive Features**: 
  - Sortable issue tables with severity filtering
  - Component-based categorization
  - Rule-based issue classification
  - Direct server API integration

#### SBOM (Software Bill of Materials)
- **Upload Format**: CycloneDX JSON/XML
- **Analysis Capabilities**: Component inventory, license compliance, dependency mapping
- **Interactive Features**: 
  - Component details table with metadata
  - License analysis and compliance tracking
  - Component search and type filtering
  - Enhanced XML namespace handling

#### Trivy Container Scans
- **Upload Format**: JSON from Trivy CLI
- **Analysis Capabilities**: Container vulnerabilities, package-level issues, CVSS scoring
- **Interactive Features**: 
  - Resizable vulnerability tables
  - CVE linking to NIST database
  - Package search and severity filtering
  - Sticky headers for large datasets

### Advanced Functionality

#### Interactive Data Tables
- **Real-time Filtering**: Search across all columns
- **Multi-level Sorting**: Click headers for ascending/descending sort
- **Responsive Design**: Horizontal scrolling for wide tables
- **Resizable Interface**: Drag table borders to adjust height (Trivy)

#### Data Export Options
- **PDF Reports**: Print-optimized layouts for executive reporting
- **JSON Export**: Structured data for programmatic access
- **Compliance Ready**: Formatted outputs for audit requirements

## API Integration

### SonarQube Server Integration
Configure direct connectivity to SonarQube servers:

```bash
export SONARQUBE_URL="https://sonar.company.com"
export SONARQUBE_TOKEN="your-authentication-token"
```

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | POST | Create new project |
| `/project/{id}/upload` | POST | Upload security reports |
| `/project/{id}/summary` | GET | Get project metrics |
| `/project/{id}/webhook` | POST | External integration webhook |
| `/api/health` | GET | Health check for monitoring |

### Jenkins CI/CD Integration

```bash
python scripts/jenkins-integration.py \
  --dashboard-url "https://dashboard.company.com" \
  --project-name "microservice-auth" \
  --sonarqube-report "reports/sonar-analysis.json" \
  --sbom-report "reports/cyclonedx-sbom.xml" \
  --trivy-report "reports/trivy-container-scan.json" \
  --build-number "${BUILD_NUMBER}"
```

## Architecture

### Application Structure
```
security-dashboard/
├── app.py                    # Flask application with route handlers
├── main.py                   # Application entry point
├── models.py                 # SQLAlchemy database models
├── reprocess_sbom.py         # Data migration utilities
├── templates/                # Jinja2 templates with enhanced UI
│   ├── base.html            # Bootstrap-based responsive layout
│   ├── home.html            # Project overview dashboard
│   ├── project_dashboard.html # Project summary with metrics
│   ├── sonarqube_detail.html # SonarQube analysis interface
│   ├── sbom_detail.html     # SBOM component analysis
│   └── trivy_detail.html    # Trivy vulnerability interface
├── static/                   # Frontend assets and styling
│   ├── css/dashboard.css    # Custom themes and responsive design
│   └── js/dashboard.js      # Interactive functionality and charts
├── utils/                    # Core processing modules
│   ├── parsers.py           # Multi-format report parsers
│   └── sonarqube_client.py  # SonarQube API integration
├── scripts/                  # Automation and CI/CD integration
│   └── jenkins-integration.py # Pipeline automation script
├── k8s/                     # Kubernetes deployment manifests
└── uploads/                 # Temporary file storage
```

### Database Schema
- **projects**: Project metadata with SonarQube integration keys
- **reports**: Polymorphic report storage with JSON data fields
- **Optimized Indexing**: Query optimization for large datasets

### Security Implementation
- **Input Validation**: Comprehensive file type and content verification
- **SQL Injection Prevention**: Parameterized queries throughout application
- **Session Security**: Secure cookie configuration and CSRF protection
- **API Authentication**: Token-based access control for external integrations
- **Data Sanitization**: XSS prevention in all user inputs

## Configuration

### Environment Variables
```bash
# Required Configuration
DATABASE_URL=postgresql://user:pass@host:5432/security_dashboard
SESSION_SECRET=your-cryptographically-secure-random-key

# Optional SonarQube Integration
SONARQUBE_URL=https://sonar.company.com
SONARQUBE_TOKEN=your-sonarqube-authentication-token

# Application Settings
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=50MB
FLASK_ENV=production
```

### Feature Configuration
- **SonarQube API Integration**: Enable direct server connectivity
- **Webhook Support**: External system notifications and callbacks
- **Debug Mode**: Enhanced logging and error details for development

## Development

### Adding New Report Types

1. **Parser Implementation**: Add parsing logic in `utils/parsers.py`
2. **Database Extension**: Extend report schema if required
3. **Upload Handler**: Add route processing in `app.py`
4. **UI Template**: Create dedicated detail view template
5. **Dashboard Integration**: Add summary cards and visualization

### Code Quality Standards
- **Python**: PEP 8 compliance with type hints
- **JavaScript**: ES6+ with consistent formatting
- **Templates**: Semantic HTML with accessibility considerations
- **CSS**: BEM methodology with responsive design principles

### Testing Framework
```bash
# Unit tests for report parsers
python -m pytest tests/test_parsers.py -v

# Integration tests for API endpoints
python -m pytest tests/test_api.py -v

# Frontend functionality tests
npm run test
```

## Performance & Monitoring

### Optimization Features
- **Database Indexing**: Optimized queries for large report datasets
- **Streaming Parsers**: Memory-efficient processing for large files
- **Frontend Optimization**: Lazy loading and pagination for large tables
- **Session Caching**: Repeated query optimization

### Health Monitoring
- **Kubernetes Probes**: Readiness and liveness endpoint monitoring
- **Database Health**: Connection pool and query performance tracking
- **File Processing**: Upload size limits and processing time monitoring
- **Error Tracking**: Structured logging with categorized error handling

## Deployment

### Production Requirements
- **Database**: PostgreSQL 12+ with connection pooling
- **Storage**: Persistent volumes for uploaded report files
- **Memory**: 2GB+ recommended for large report processing
- **Security**: TLS termination and security headers configuration

### Scaling Strategies
- **Horizontal Scaling**: Multiple application instances with load balancing
- **Database Optimization**: Read replicas for analytics and reporting queries
- **File Storage**: Object storage integration for uploaded reports
- **Caching Layer**: Redis integration for session and query caching

## Troubleshooting

### Common Issues
- **Upload Failures**: Verify file format compliance and size limits
- **SonarQube Connection**: Check server URL and token configuration
- **Database Connectivity**: Validate connection string and permissions
- **Chart Rendering**: Ensure JavaScript libraries load correctly

### Debug Configuration
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
python main.py
```

### Log Analysis
- **Application Logs**: Structured JSON logging for analysis
- **Database Queries**: Query performance monitoring
- **Upload Processing**: File validation and parsing error tracking

## Recent Updates (Current Release)

### Enhanced SBOM Processing
- Improved XML parser with multi-namespace support
- Component details table with comprehensive metadata
- License analysis and compliance tracking
- Enhanced component search and filtering

### Trivy Interface Improvements
- Resizable table containers with sticky headers
- Enhanced CVE linking and CVSS score display
- Improved package name styling and severity badges
- Better mobile responsiveness and compact design

### User Interface Enhancements
- Upload buttons for each report type with validation
- Improved table layouts with space-efficient design
- Enhanced color contrast and typography
- Responsive design optimizations

## Contributing

1. **Development Setup**: Follow local development installation guide
2. **Code Standards**: Maintain consistency with existing patterns
3. **Testing Requirements**: Include comprehensive tests for new features
4. **Documentation**: Update relevant documentation sections
5. **Pull Requests**: Provide detailed descriptions and testing evidence

## License

MIT License - see LICENSE file for comprehensive terms

## Support

- **Issue Tracking**: GitHub repository issue tracker
- **Documentation**: Comprehensive in-code documentation and examples
- **Community**: Developer community support and contributions