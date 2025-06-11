# Deployment Guide

This guide covers different deployment options for the Security Dashboard.

## Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/yourusername/security-dashboard.git
cd security-dashboard

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and configuration

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Run application
python main.py
```

## Production Deployment

### Docker Deployment

1. **Build Image**
```bash
docker build -t security-dashboard:1.0.0 .
```

2. **Run with Docker Compose**
```bash
docker-compose up -d
```

3. **Environment Configuration**
Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  web:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/security_dashboard
      - SESSION_SECRET=your-production-secret
  db:
    environment:
      - POSTGRES_DB=security_dashboard
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

### Kubernetes Deployment

1. **Deploy to Cluster**
```bash
kubectl apply -f k8s/
```

2. **Configure Secrets**
```bash
kubectl create secret generic security-dashboard-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/security_dashboard" \
  --from-literal=session-secret="your-production-secret"
```

3. **Verify Deployment**
```bash
kubectl get pods -l app=security-dashboard
kubectl get services security-dashboard-service
```

### Cloud Platform Deployment

#### Google Cloud Platform (GKE)

1. **Create GKE Cluster**
```bash
gcloud container clusters create security-dashboard-cluster \
  --num-nodes=3 \
  --zone=us-central1-a
```

2. **Deploy Application**
```bash
kubectl apply -f k8s/
```

3. **Set up Load Balancer**
```bash
kubectl expose deployment security-dashboard \
  --type=LoadBalancer \
  --port=80 \
  --target-port=5000
```

#### AWS EKS

1. **Create EKS Cluster**
```bash
eksctl create cluster --name security-dashboard --region us-west-2
```

2. **Deploy Application**
```bash
kubectl apply -f k8s/
```

#### Azure AKS

1. **Create AKS Cluster**
```bash
az aks create \
  --resource-group myResourceGroup \
  --name security-dashboard-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

## Database Setup

### PostgreSQL Configuration

1. **Create Database**
```sql
CREATE DATABASE security_dashboard;
CREATE USER dashboard_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE security_dashboard TO dashboard_user;
```

2. **Initialize Schema**
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Database Migration

For production deployments, use proper migration tools:
```bash
# Example with Flask-Migrate (if added)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Security Configuration

### SSL/TLS Setup

1. **Certificate Generation**
```bash
# Let's Encrypt with Certbot
certbot --nginx -d your-domain.com
```

2. **Nginx Configuration**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Security

1. **Secure Secret Management**
```bash
# Use Kubernetes secrets
kubectl create secret generic app-secrets \
  --from-literal=session-secret="$(openssl rand -hex 32)" \
  --from-literal=database-password="$(openssl rand -base64 32)"
```

2. **Environment Variables**
```bash
# Production environment
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECURE_SSL_REDIRECT=True
```

## Monitoring and Logging

### Application Monitoring

1. **Health Check Endpoint**
```bash
curl http://your-domain.com/health
```

2. **Metrics Collection**
```yaml
# Prometheus configuration
scrape_configs:
  - job_name: 'security-dashboard'
    static_configs:
      - targets: ['security-dashboard:5000']
```

### Log Management

1. **Structured Logging**
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
```

2. **Log Aggregation**
```yaml
# Filebeat configuration for ELK stack
filebeat.inputs:
- type: log
  paths:
    - /var/log/security-dashboard/*.log
```

## Performance Optimization

### Database Optimization

1. **Connection Pooling**
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 300,
    'pool_pre_ping': True
}
```

2. **Index Optimization**
```sql
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_reports_project_id ON reports(project_id);
```

### Application Scaling

1. **Horizontal Scaling**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: security-dashboard
```

2. **Load Balancing**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: security-dashboard-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 5000
  selector:
    app: security-dashboard
```

## Backup and Recovery

### Database Backup

1. **Automated Backups**
```bash
# Daily backup script
pg_dump security_dashboard > backup_$(date +%Y%m%d).sql
```

2. **Backup to Cloud Storage**
```bash
# AWS S3 backup
aws s3 cp backup_$(date +%Y%m%d).sql s3://your-backup-bucket/
```

### Disaster Recovery

1. **Database Restore**
```bash
psql security_dashboard < backup_20250611.sql
```

2. **Application Recovery**
```bash
kubectl rollout undo deployment/security-dashboard
```

## Troubleshooting

### Common Issues

1. **Database Connection**
```bash
# Test database connectivity
psql $DATABASE_URL -c "SELECT 1;"
```

2. **Application Logs**
```bash
# Kubernetes logs
kubectl logs -f deployment/security-dashboard

# Docker logs
docker logs security-dashboard
```

3. **Performance Issues**
```bash
# Check resource usage
kubectl top pods
kubectl describe pod security-dashboard-xxx
```

### Debug Mode

For development troubleshooting:
```bash
export FLASK_DEBUG=True
export LOG_LEVEL=DEBUG
python main.py
```

## Maintenance

### Regular Updates

1. **Security Updates**
```bash
# Update dependencies
pip list --outdated
pip install --upgrade package-name
```

2. **Database Maintenance**
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM projects WHERE created_at > NOW() - INTERVAL '7 days';

-- Vacuum database
VACUUM ANALYZE;
```

### Monitoring Checklist

- [ ] Application health endpoints responding
- [ ] Database connections stable
- [ ] SSL certificates valid
- [ ] Backup processes running
- [ ] Log files not exceeding disk space
- [ ] Security updates applied
- [ ] Performance metrics within normal ranges