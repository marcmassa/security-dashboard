# SonarQube Integration Guide - Security Dashboard

## Recomendaciones para Obtener Datos de SonarQube

### **Opción 1: API REST de SonarQube (RECOMENDADO)**

Esta es la mejor opción para obtener datos completos y actualizados directamente del servidor SonarQube.

#### **Ventajas:**
- **Datos en tiempo real** directamente del servidor
- **Issues detallados** con ubicación exacta en código (archivo, línea)
- **Métricas históricas** y tendencias
- **Quality Gates** y reglas aplicadas
- **Security Hotspots** con contexto completo
- **Automatización completa** sin archivos intermedios

#### **Configuración Necesaria:**

1. **Token de Autenticación**
   ```bash
   # En SonarQube: User > My Account > Security > Generate Tokens
   # Crear token de tipo "User Token" o "Project Analysis Token"
   ```

2. **Project Key**
   ```bash
   # En SonarQube: Project > Project Information > Project Key
   # Ejemplo: com.company:my-project
   ```

3. **URLs de API Utilizadas**
   ```bash
   # Métricas del proyecto
   GET /api/measures/component?component=PROJECT_KEY&metricKeys=bugs,vulnerabilities,code_smells
   
   # Issues detallados
   GET /api/issues/search?componentKeys=PROJECT_KEY&types=BUG,VULNERABILITY
   
   # Security Hotspots
   GET /api/hotspots/search?projectKey=PROJECT_KEY
   ```

#### **Uso en Dashboard:**
1. Ir a un proyecto existente
2. Navegar a la vista detallada de SonarQube
3. Hacer clic en "Connect to SonarQube"
4. Completar el formulario con:
   - **Server URL**: `https://sonarqube.tuempresa.com`
   - **Token**: Tu token de autenticación
   - **Project Key**: Clave del proyecto a analizar

### **Opción 2: Archivo JSON desde Pipeline CI/CD**

Para integración automatizada en pipelines Jenkins/GitLab CI.

#### **Jenkins Pipeline:**
```groovy
pipeline {
    stages {
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'mvn sonar:sonar -Dsonar.projectKey=${PROJECT_KEY}'
                }
                
                // Obtener reporte después del análisis
                script {
                    sh """
                        curl -u \${SONAR_AUTH_TOKEN}: \\
                        "\${SONAR_HOST_URL}/api/measures/component?component=\${PROJECT_KEY}&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_rating,reliability_rating,security_rating" \\
                        > sonarqube-report.json
                    """
                }
            }
        }
        
        stage('Upload to Dashboard') {
            steps {
                script {
                    sh """
                        python3 scripts/jenkins-integration.py \\
                            --dashboard-url \${DASHBOARD_URL} \\
                            --project-name \${JOB_NAME} \\
                            --sonarqube-report sonarqube-report.json
                    """
                }
            }
        }
    }
}
```

#### **GitLab CI:**
```yaml
sonarqube_analysis:
  stage: test
  script:
    - sonar-scanner -Dsonar.projectKey=$PROJECT_KEY
    - |
      curl -u $SONAR_TOKEN: \
      "$SONAR_HOST_URL/api/measures/component?component=$PROJECT_KEY&metricKeys=bugs,vulnerabilities,code_smells,coverage" \
      > sonarqube-report.json
  artifacts:
    reports:
      junit: sonarqube-report.json
```

### **Opción 3: SonarQube Scanner con Export**

Para proyectos que ejecutan análisis local.

```bash
# Ejecutar análisis
sonar-scanner \
  -Dsonar.projectKey=mi-proyecto \
  -Dsonar.sources=src \
  -Dsonar.host.url=https://sonarqube.empresa.com \
  -Dsonar.login=$SONAR_TOKEN

# Esperar a que termine y exportar
curl -u $SONAR_TOKEN: \
  "https://sonarqube.empresa.com/api/measures/component?component=mi-proyecto&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_rating,reliability_rating,security_rating,quality_gate_status" \
  > sonarqube-export.json
```

## **Comparación de Opciones**

| Característica | API REST | Archivo CI/CD | Scanner Local |
|----------------|----------|---------------|---------------|
| **Datos en tiempo real** | ✅ | ✅ | ✅ |
| **Issues detallados** | ✅ | ✅ | ✅ |
| **Automatización** | ✅ | ✅ | ⚠️ Manual |
| **Histórico** | ✅ | ❌ | ❌ |
| **Security Hotspots** | ✅ | ⚠️ Limitado | ⚠️ Limitado |
| **Facilidad de uso** | ✅ | ⚠️ Configuración | ⚠️ Manual |

## **Estructura de Datos Recomendada**

### **Métricas Básicas (API /measures/component)**
```json
{
  "component": {
    "key": "com.company:project",
    "name": "My Project",
    "measures": [
      {"metric": "bugs", "value": "5"},
      {"metric": "vulnerabilities", "value": "2"},
      {"metric": "code_smells", "value": "23"},
      {"metric": "coverage", "value": "85.2"},
      {"metric": "duplicated_lines_density", "value": "3.5"},
      {"metric": "sqale_rating", "value": "A"},
      {"metric": "reliability_rating", "value": "B"},
      {"metric": "security_rating", "value": "A"},
      {"metric": "quality_gate_status", "value": "OK"}
    ]
  }
}
```

### **Issues Detallados (API /issues/search)**
```json
{
  "issues": [
    {
      "key": "issue-key-123",
      "rule": "java:S1234",
      "severity": "MAJOR",
      "component": "com.company:project:src/main/java/Main.java",
      "line": 42,
      "message": "Remove this unused variable",
      "type": "CODE_SMELL",
      "status": "OPEN",
      "creationDate": "2023-12-01T10:30:00+0000"
    }
  ]
}
```

### **Security Hotspots (API /hotspots/search)**
```json
{
  "hotspots": [
    {
      "key": "hotspot-123",
      "component": "com.company:project:src/main/java/Security.java",
      "line": 15,
      "message": "Review this potentially vulnerable code",
      "status": "TO_REVIEW",
      "vulnerabilityProbability": "HIGH"
    }
  ]
}
```

## **Mi Recomendación Final**

**Para tu caso de uso, recomiendo la Opción 1 (API REST) porque:**

1. **Datos Auténticos Completos**: Obtienes toda la información disponible
2. **Issues con Contexto**: Ubicación exacta en archivos y líneas de código
3. **Interfaz de Usuario**: Modal integrado para conectar fácilmente
4. **Flexibilidad**: Puedes actualizar datos cuando quieras
5. **Integración CI/CD**: También funciona desde Jenkins con el endpoint API

### **Próximos Pasos:**

1. **Configura tu token SonarQube**:
   - Ve a tu perfil en SonarQube
   - Genera un token de usuario
   - Guarda el token de forma segura

2. **Identifica tu Project Key**:
   - Ve al proyecto en SonarQube  
   - Copia el Project Key desde Project Information

3. **Prueba la conexión**:
   - Crea un proyecto en el dashboard
   - Usa el botón "Connect to SonarQube"
   - Verifica que los datos se cargan correctamente

4. **Automatiza con Jenkins** (opcional):
   - Usa el endpoint `/api/projects/{id}/sonarqube/fetch`
   - Integra en tu pipeline existente

¿Te gustaría que te ayude a configurar alguna de estas opciones específicamente?