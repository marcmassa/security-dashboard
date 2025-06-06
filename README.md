# Security Analysis Dashboard

Dashboard de análisis de seguridad que agrega y visualiza datos de reportes SonarQube, SBOM y Trivy usando Flask y PostgreSQL, diseñado para despliegue en Kubernetes.

## Características

- **Multi-formato**: Soporta reportes SonarQube (JSON), SBOM CycloneDX (JSON/XML), Trivy (JSON/HTML)
- **Visualización**: Dashboards interactivos con Chart.js y Bootstrap
- **Persistencia**: Base de datos PostgreSQL para almacenamiento de reportes
- **APIs REST**: Endpoints para integración con CI/CD (Jenkins)
- **Containerizado**: Listo para despliegue en Kubernetes/GKE
- **Escalable**: Configurado con autoescalado horizontal

## Arquitectura

```
Frontend (Flask Templates) → Backend (Flask API) → Database (PostgreSQL)
                     ↓
            Jenkins Integration ← Container Registry (GCR)
                     ↓
             Kubernetes (GKE) → Load Balancer
```

## Inicio Rápido

### Desarrollo Local
```bash
# Clonar repositorio
git clone <repository-url>
cd security-dashboard

# Usando Docker Compose
docker-compose up -d

# Acceder a http://localhost:5000
```

### Despliegue en GKE
```bash
# 1. Construir y subir imagen
./scripts/build-and-push.sh YOUR_PROJECT_ID

# 2. Desplegar en cluster
./scripts/deploy-gke.sh YOUR_PROJECT_ID cluster-name zone
```

## Estructura del Proyecto

```
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── utils/
│   └── parsers.py         # Parsers para reportes de seguridad
├── templates/             # Templates HTML
├── static/                # CSS, JS, assets
├── k8s/                   # Manifiestos Kubernetes
├── scripts/               # Scripts de despliegue
├── Dockerfile             # Imagen Docker
└── docker-compose.yml     # Desarrollo local
```

## APIs Disponibles

### Gestión de Proyectos
- `GET /` - Lista de proyectos
- `POST /api/projects/find-or-create` - Buscar/crear proyecto
- `GET /project/{id}` - Dashboard del proyecto
- `GET /api/projects/{id}/status` - Estado del proyecto

### Carga de Reportes
- `POST /project/{id}/upload` - Subir reporte de seguridad
- `GET /project/{id}/api/summary` - Resumen de métricas

### Integración CI/CD
- `POST /api/projects/{id}/webhook` - Notificaciones Jenkins
- `GET /health` - Health check para Kubernetes

## Integración con Jenkins

### Pipeline Ejemplo
```groovy
stage('Upload Security Reports') {
    steps {
        sh '''
            python3 scripts/jenkins-integration.py \
                --dashboard-url https://dashboard.example.com \
                --project-name ${JOB_NAME} \
                --sonarqube-report sonar-report.json \
                --trivy-report trivy-report.json \
                --jenkins-build ${BUILD_NUMBER} \
                --jenkins-url ${BUILD_URL}
        '''
    }
}
```

### Script de Integración
```bash
# Subir reportes desde Jenkins
python3 scripts/jenkins-integration.py \
    --dashboard-url http://dashboard-url \
    --project-name mi-proyecto \
    --sonarqube-report reports/sonar.json \
    --sbom-report reports/sbom.json \
    --trivy-report reports/trivy.json
```

## Configuración

### Variables de Entorno
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
SESSION_SECRET=your-secret-key
FLASK_ENV=production
```

### Kubernetes Secrets
```bash
kubectl create secret generic security-dashboard-secrets \
    --from-literal=DATABASE_URL="postgresql://..." \
    --from-literal=SESSION_SECRET="..." \
    --namespace=security-dashboard
```

## Formatos de Reportes Soportados

### SonarQube
```json
{
  "component": {
    "measures": [
      {"metric": "bugs", "value": "0"},
      {"metric": "vulnerabilities", "value": "2"},
      {"metric": "code_smells", "value": "15"}
    ]
  }
}
```

### SBOM (CycloneDX)
```json
{
  "bomFormat": "CycloneDX",
  "components": [...],
  "vulnerabilities": [...]
}
```

### Trivy
```json
{
  "Results": [
    {
      "Target": "image:latest",
      "Vulnerabilities": [...]
    }
  ]
}
```

## Monitoreo

### Health Checks
```bash
# Local
curl http://localhost:5000/health

# Kubernetes
kubectl get pods -n security-dashboard
kubectl logs -f deployment/security-dashboard -n security-dashboard
```

### Métricas
- Autoescalado basado en CPU/memoria
- Health checks configurados
- Logging centralizado

## Desarrollo

### Prerequisitos
- Python 3.11+
- PostgreSQL
- Docker & Docker Compose
- kubectl (para despliegue)

### Configuración Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno
export DATABASE_URL="postgresql://localhost/security_dashboard"
export SESSION_SECRET="dev-secret"

# Inicializar base de datos
python -c "from app import db; db.create_all()"

# Ejecutar aplicación
python app.py
```

### Testing
```bash
# Ejecutar tests
python -m pytest tests/

# Linting
flake8 app.py models.py utils/

# Análisis de seguridad
bandit -r .
```

## Documentación Adicional

- [Guía de Despliegue](DEPLOYMENT.md) - Instrucciones detalladas para GKE
- [Arquitectura](ARCHITECTURE.md) - Diagramas y especificaciones técnicas

## Contribuir

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

MIT License - ver archivo LICENSE para detalles.