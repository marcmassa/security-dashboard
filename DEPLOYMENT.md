# Security Dashboard - Guía de Despliegue en Kubernetes (GKE)

## Arquitectura de Microservicios

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Ingress       │    │   GKE Cluster   │
│   (Cloud LB)    │◄──►│   (GCE)         │◄──►│                 │
└─────────────────┘    └─────────────────┘    │ ┌─────────────┐ │
                                              │ │ Dashboard   │ │
┌─────────────────┐    ┌─────────────────┐    │ │ Pods (3x)   │ │
│   Jenkins       │    │   Container     │    │ └─────────────┘ │
│   Pipeline      │◄──►│   Registry      │    │                 │
└─────────────────┘    │   (GCR)         │    │ ┌─────────────┐ │
                       └─────────────────┘    │ │ PostgreSQL  │ │
                                              │ │ Pod         │ │
                                              │ └─────────────┘ │
                                              └─────────────────┘
```

## Prerrequisitos

### 1. Herramientas Requeridas
```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# kubectl
gcloud components install kubectl

# Docker
# Instalar según tu sistema operativo
```

### 2. Configuración GCP
```bash
# Autenticación
gcloud auth login
gcloud auth configure-docker

# Crear proyecto (opcional)
gcloud projects create my-security-dashboard --name="Security Dashboard"
gcloud config set project my-security-dashboard

# Habilitar APIs necesarias
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable compute.googleapis.com
```

### 3. Crear Cluster GKE
```bash
# Cluster con autoescalado
gcloud container clusters create security-dashboard-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=10 \
    --machine-type=e2-standard-2 \
    --enable-autorepair \
    --enable-autoupgrade
```

## Proceso de Despliegue

### Opción 1: Despliegue Automatizado

```bash
# 1. Construir y subir imagen
./scripts/build-and-push.sh YOUR_PROJECT_ID latest

# 2. Desplegar en GKE
./scripts/deploy-gke.sh YOUR_PROJECT_ID security-dashboard-cluster us-central1-a latest
```

### Opción 2: Despliegue Manual

#### Paso 1: Construir Imagen Docker
```bash
# Construir imagen
docker build -t gcr.io/YOUR_PROJECT_ID/security-dashboard:latest .

# Subir a Container Registry
docker push gcr.io/YOUR_PROJECT_ID/security-dashboard:latest
```

#### Paso 2: Actualizar Configuración
```bash
# Actualizar imagen en deployment
sed -i 's|gcr.io/PROJECT_ID/security-dashboard:latest|gcr.io/YOUR_PROJECT_ID/security-dashboard:latest|g' k8s/deployment.yaml

# Actualizar secretos y configuración
kubectl create secret generic security-dashboard-secrets \
    --from-literal=DATABASE_URL="postgresql://dashboard_user:secure-postgres-password@postgres:5432/security_dashboard" \
    --from-literal=SESSION_SECRET="your-production-secret-key" \
    --namespace=security-dashboard
```

#### Paso 3: Desplegar Aplicación
```bash
# Aplicar manifiestos en orden
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml

# Esperar PostgreSQL
kubectl wait --for=condition=ready pod -l app=postgres -n security-dashboard --timeout=300s

# Desplegar aplicación
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## Configuración de Producción

### 1. Variables de Entorno Críticas
```yaml
# k8s/secret.yaml (actualizar valores)
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/security_dashboard"
  SESSION_SECRET: "production-secret-key-256-bits"
```

### 2. Recursos y Límites
```yaml
# Ajustar según carga esperada
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### 3. Configurar Ingress con HTTPS
```bash
# Reservar IP estática
gcloud compute addresses create security-dashboard-ip --global

# Actualizar k8s/ingress.yaml con tu dominio
# Aplicar certificado SSL
kubectl apply -f k8s/ingress.yaml
```

## Monitoreo y Observabilidad

### Health Checks
```bash
# Verificar estado de pods
kubectl get pods -n security-dashboard

# Verificar logs
kubectl logs -f deployment/security-dashboard -n security-dashboard

# Probar health endpoint
kubectl port-forward service/security-dashboard-service 8080:80 -n security-dashboard
curl http://localhost:8080/health
```

### Métricas de Autoescalado
```bash
# Ver estado del HPA
kubectl get hpa -n security-dashboard

# Ver métricas actuales
kubectl top pods -n security-dashboard
```

## Integración con Jenkins

### 1. Pipeline de CI/CD
```groovy
pipeline {
    agent any
    
    environment {
        PROJECT_ID = 'your-gcp-project'
        CLUSTER_NAME = 'security-dashboard-cluster'
        CLUSTER_ZONE = 'us-central1-a'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Build & Test') {
            steps {
                sh 'docker build -t gcr.io/${PROJECT_ID}/security-dashboard:${IMAGE_TAG} .'
            }
        }
        
        stage('Security Scan') {
            parallel {
                stage('SonarQube') {
                    steps {
                        withSonarQubeEnv('SonarQube') {
                            sh 'sonar-scanner'
                        }
                    }
                }
                
                stage('Container Scan') {
                    steps {
                        sh 'trivy image gcr.io/${PROJECT_ID}/security-dashboard:${IMAGE_TAG}'
                    }
                }
            }
        }
        
        stage('Push Image') {
            steps {
                sh 'docker push gcr.io/${PROJECT_ID}/security-dashboard:${IMAGE_TAG}'
            }
        }
        
        stage('Deploy') {
            steps {
                sh '''
                    gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${CLUSTER_ZONE}
                    kubectl set image deployment/security-dashboard security-dashboard=gcr.io/${PROJECT_ID}/security-dashboard:${IMAGE_TAG} -n security-dashboard
                    kubectl rollout status deployment/security-dashboard -n security-dashboard
                '''
            }
        }
        
        stage('Upload Reports') {
            steps {
                script {
                    // Subir reportes al dashboard
                    def dashboardUrl = sh(
                        script: "kubectl get service security-dashboard-service -n security-dashboard -o jsonpath='{.status.loadBalancer.ingress[0].ip}'",
                        returnStdout: true
                    ).trim()
                    
                    sh """
                        python3 scripts/jenkins-integration.py \
                            --dashboard-url http://${dashboardUrl} \
                            --project-name ${JOB_NAME} \
                            --sonarqube-report sonar-report.json \
                            --trivy-report trivy-report.json
                    """
                }
            }
        }
    }
}
```

### 2. Script de Integración Jenkins
```python
#!/usr/bin/env python3
import requests
import argparse
import sys
import os

def upload_reports(dashboard_url, project_name, reports):
    client = SecurityDashboardClient(dashboard_url)
    
    try:
        project_id = client.find_or_create_project(project_name)
        print(f"Project ID: {project_id}")
        
        for report_type, file_path in reports.items():
            if os.path.exists(file_path):
                result = client.upload_report(project_id, report_type, file_path)
                print(f"✓ {report_type} uploaded successfully")
            else:
                print(f"⚠ {report_type} report not found: {file_path}")
        
        print(f"Dashboard: {dashboard_url}/project/{project_id}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dashboard-url', required=True)
    parser.add_argument('--project-name', required=True)
    parser.add_argument('--sonarqube-report')
    parser.add_argument('--sbom-report')
    parser.add_argument('--trivy-report')
    
    args = parser.parse_args()
    
    reports = {}
    if args.sonarqube_report:
        reports['sonarqube'] = args.sonarqube_report
    if args.sbom_report:
        reports['sbom'] = args.sbom_report
    if args.trivy_report:
        reports['trivy'] = args.trivy_report
    
    upload_reports(args.dashboard_url, args.project_name, reports)
```

## Mantenimiento y Actualizaciones

### Rolling Updates
```bash
# Actualizar imagen
kubectl set image deployment/security-dashboard security-dashboard=gcr.io/PROJECT_ID/security-dashboard:new-tag -n security-dashboard

# Verificar rollout
kubectl rollout status deployment/security-dashboard -n security-dashboard

# Rollback si es necesario
kubectl rollout undo deployment/security-dashboard -n security-dashboard
```

### Backup de Base de Datos
```bash
# Backup manual
kubectl exec -n security-dashboard postgres-pod -- pg_dump -U dashboard_user security_dashboard > backup.sql

# Configurar backups automáticos con cronjob
kubectl apply -f k8s/backup-cronjob.yaml
```

### Escalado Manual
```bash
# Escalar aplicación
kubectl scale deployment security-dashboard --replicas=5 -n security-dashboard

# Escalar PostgreSQL (solo para desarrollo)
kubectl scale deployment postgres --replicas=1 -n security-dashboard
```

## Troubleshooting

### Problemas Comunes

1. **Pod no inicia**
```bash
kubectl describe pod POD_NAME -n security-dashboard
kubectl logs POD_NAME -n security-dashboard
```

2. **Base de datos no conecta**
```bash
kubectl exec -it postgres-pod -n security-dashboard -- psql -U dashboard_user -d security_dashboard
```

3. **Ingress no funciona**
```bash
kubectl describe ingress security-dashboard-ingress -n security-dashboard
```

### Logs y Debugging
```bash
# Logs en tiempo real
kubectl logs -f deployment/security-dashboard -n security-dashboard

# Acceso directo al pod
kubectl exec -it POD_NAME -n security-dashboard -- /bin/bash

# Port forward para testing local
kubectl port-forward service/security-dashboard-service 8080:80 -n security-dashboard
```

## Consideraciones de Seguridad

1. **Network Policies**: Implementar políticas de red para aislar tráfico
2. **RBAC**: Configurar roles y permisos específicos
3. **Secrets Management**: Usar Google Secret Manager para producción
4. **Container Security**: Escanear imágenes regularmente con Trivy
5. **SSL/TLS**: Usar certificados gestionados de Google para HTTPS