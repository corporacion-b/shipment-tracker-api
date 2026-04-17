# DHL-Shipment-Tracker-API

<p align="center">
  API de rastreo de envíos construida con FastAPI que consume la DHL API.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Pytest-Tests-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

---


## Problema

Consultar el estado de un envío desde distintas fuentes suele implicar respuestas poco uniformes o resultados imprecisos.

## Solucion

`shipment-tracker-api` centraliza la consulta del envío en un endpoint HTTP simple y devuelve una respuesta estructurada con el identificador, el estado actual, la ubicación y los días en espera.

## Enfoque tecnico

El servicio fue desarrollado con FastAPI y se valida con un enfoque "shift left" mediante pruebas automatizadas con `pytest` y `TestClient`. Además, el proyecto cuenta con un pipeline CI/CD que construye y publica la imagen Docker en Docker Hub para facilitar su ejecución y despliegue.

---

## Caracteristicas

- Respuestas JSON consistentes y fáciles de consumir.
- Manejo de errores para consultas inválidas o envíos no encontrados.
- Pruebas automatizadas del flujo principal.
- Contenerización con Docker.

---

## Arquitectura del servicio

<p align="center">
  <img src="./docs/arquitectura.png" alt="Diagrama de arquitectura del servicio" width="900">
</p>

La arquitectura se organiza alrededor de `shipment-tracker-api` como servicio central de consulta. Un cliente, ya sea desde Postman o desde un frontend, envía solicitudes al servicio para obtener información de rastreo. A partir de estas solicitudes, la API consume la DHL API para recuperar datos del envío, como estatus, ubicación, historial y tiempo inmóvil.

`shipment-tracker-api` consulta la DHL API, guarda datos en MySQL y los envía a `shipment-risk-analyzer` para el análisis de riesgo.

---

## Stack tecnológico del proyecto

| Categoría | Herramientas |
| --- | --- |
| Backend | Python, FastAPI |
| Testing | PyTest |
| Base de datos | MySQL, Alembic |
| Control de versiones | Git, GitHub |
| CI/CD | GitHub Actions, GitHub Secrets |
| Contenedores | Docker, Docker Compose, Docker Hub |
| Documentación y pruebas | Swagger, Postman |
| Desarrollo | VSCode |
| Gestión del proyecto | Trello, Discord |
| Herramientas de apoyo | Excalidraw, Google Docs, herramientas de IA |

---

## Pipeline CI/CD

<p align="center">
  <img src="./docs/pipeline.png" alt="Diagrama del pipeline CI/CD" width="900">
</p>

El flujo de trabajo parte de `main`, desde donde se crean ramas `feature` para nuevas funcionalidades y ramas `fix` para correcciones. Una vez desarrollado el cambio, este se integra mediante un pull request hacia `develop`, donde pasa por una etapa de revisión en parejas, validación de comportamiento y pruebas unitarias.

Si la revisión o las pruebas fallan, el flujo regresa a una rama de corrección para ajustar el cambio antes de volver a evaluarlo. Cuando el cambio es aprobado, entra a la fase de despliegue e integración, donde GitHub Actions ejecuta el workflow, levanta un entorno de prueba similar a producción, corre pruebas automatizadas, construye la imagen Docker y la publica. Finalmente, tras completar el proceso, los cambios se integran en `main`.

---

## Estructura del proyecto

```text
shipment-tracker-api/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── # Código fuente de la API
├── tests/
│   └── # Pruebas automatizadas
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Requisitos previos

- Python 3.10 o superior
- `pip`
- Git
- Docker
- Docker Compose
- Credenciales de acceso a la DHL API
- Variables de entorno configuradas

Antes de ejecutar el proyecto, asegúrate de contar con acceso a la DHL API, definir las variables necesarias y tener disponible un entorno local o en contenedor para la base de datos y la aplicación.

---

## Variables de entorno

El proyecto usa variables de entorno para configurar la aplicación, la base de datos y la integración con la DHL API. En local, estas variables se definen en un archivo `.env`.

Para CI/CD, los datos sensibles no se guardan en el repositorio. En su lugar, se almacenan en `GitHub Secrets` para que el pipeline pueda usarlos de forma segura.

### Ejemplo de archivo `.env`

```env
# APP
APP_ENV=development
APP_PORT=8000

# DATABASE
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=secret
MYSQL_DATABASE=shipments

# DHL API
DHL_API_KEY=your_api_key
DHL_BASE_URL=https://api.dhl.com

# DOCKER
DOCKER_IMAGE_NAME=erickyamilrc/shipment-tracker-api
DOCKER_IMAGE_TAG=latest
DOCKERHUB_USERNAME=your_dockerhub_user
DOCKERHUB_TOKEN=your_dockerhub_token
```

---

## Ejecucion local

```bash
git clone https://github.com/corporacion-b/shipment-tracker-api.git
cd shipment-tracker-api
pip install -r requirements.txt
uvicorn src.main:src --reload
```

La API quedará disponible en `http://127.0.0.1:8000`.

---

## Ejecucion con Docker

Docker permite ejecutar la aplicación a partir de una imagen ya publicada, evitando instalaciones manuales y facilitando un entorno consistente. En este proyecto, la imagen se distribuye a través de Docker Hub para simplificar su uso en desarrollo o despliegue.

### Descarga de la imagen

```bash
docker pull erickyamilrc/shipment-tracker-api:latest
```

Este comando:

- descarga desde Docker Hub la versión más reciente de la imagen del proyecto
- deja la imagen disponible en tu entorno local para poder ejecutarla
- garantiza que utilices la imagen publicada por el pipeline CI/CD
- evita tener que construir la imagen manualmente desde el `Dockerfile`

### Ejecucion del contenedor

```bash
docker run -p 8000:8000 erickyamilrc/shipment-tracker-api:latest
```

Este comando:

- crea e inicia un contenedor a partir de la imagen `erickyamilrc/shipment-tracker-api:latest`
- expone el puerto `8000` del contenedor en el puerto `8000` de tu maquina
- permite acceder a la API desde `http://127.0.0.1:8000`

Una vez iniciado el contenedor, puedes verificar que la API está disponible accediendo a `/docs`, donde se expone la documentación interactiva generada por FastAPI.

---

## Endpoints disponibles

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | `/shipment/{id}/status` | Obtiene el estado actual del paquete. |
| GET | `/shipment/{id}/location` | Devuelve la ubicación actual del envío. |
| GET | `/shipment/{id}/history` | Lista cronológicamente los puntos de control del paquete. |
| GET | `/shipment/{id}/dwell-time` | Calcula el tiempo que el paquete ha permanecido inmóvil en la ubicación actual. |

### Ejemplo de respuesta JSON: `/shipment/{id}/status`

```json
{
  "tracking_id": "DHL-123",
  "status": "En transito"
}
```

### Ejemplo de respuesta JSON: `/shipment/{id}/location`

```json
{
  "tracking_id": "DHL-123",
  "location": "Madrid"
}
```

### Ejemplo de respuesta JSON: `/shipment/{id}/history`

```json
{
  "tracking_id": "DHL-123",
  "history": [
    "Ciudad de origen",
    "Centro logístico",
    "Aduana",
    "Ciudad de destino"
  ]
}
```

### Ejemplo de respuesta JSON: `/shipment/{id}/dwell-time`

```json
{
  "tracking_id": "DHL-123",
  "days_stationary": 2
}
```

### Manejo de errores

| Código | Descripción |
| --- | --- |
| `400 Bad Request` | El formato del `id` es inválido o faltan parámetros obligatorios. |
| `401/403 Unauthorized` | Fallo en la autenticación o falta de permisos para consultar el envío. |
| `404 Not Found` | El número de guía no existe en los registros de DHL. |
| `429 Too Many Requests` | El cliente ha excedido el límite de peticiones permitido. |
| `500 Internal Server Error` | Error genérico no controlado en el servidor. |
| `502 Bad Gateway` | La API de DHL devolvió una respuesta inválida o inesperada. |
| `503 Service Unavailable` | La API de DHL no responde o se encuentra en mantenimiento. |

---

## Documentación automática

- Swagger UI: `http://127.0.0.1:8000/docs`
- Esta interfaz permite explorar los endpoints, probar solicitudes y revisar los modelos de respuesta desde el navegador.

---

## Pruebas

```bash
pytest
```

Las pruebas cubren:

- Consulta del estado actual del envío.
- Obtencion de la ubicacion actual del paquete.
- Recuperación del historial de checkpoints del envío.
- Cálculo del tiempo inmóvil en la ubicación actual.

Estas pruebas permiten validar el comportamiento esperado de los endpoints principales y detectar regresiones de forma temprana durante el desarrollo.

---

## Integrantes

| Rol | Nombre |
| --- | --- |
| Tech Lead | Enrique Vido |
| Backend | Josue Rosaldo |
| QA/DevOps | Erick Rodriguez |
| Docs | Maria Montserrat |
