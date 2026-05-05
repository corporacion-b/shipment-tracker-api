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
PROJECT_NAME=Shipment Tracker API
DHL_API_KEY=your_dhl_api_key
DHL_API_SECRET=your_dhl_api_secret
DHL_BASE_URL=https://api-eu.dhl.com/track/shipments
DATABASE_URL=mysql://root:secret@127.0.0.1:3307/shipments
```
---

## Desarrollo local

### 1. Levantar MySQL

Desde la raíz del proyecto:

```bash
docker compose up -d mysql
```

Esto crea un contenedor MySQL 8 con:

- host: `localhost`
- puerto: `3307`
- usuario: `root`
- contraseña: `secret`
- base de datos: `shipments`


### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 3. Arrancar la API

```bash
uvicorn src.main:src --reload
```

Para ejecución local, `DATABASE_URL` debe apuntar a MySQL expuesto en tu máquina:

```env
DATABASE_URL=mysql://root:secret@127.0.0.1:3307/shipments
```

La API queda disponible en:

```text
http://127.0.0.1:8000
```

---

## Ejecución con imagen Docker

### 1. Descargar la imagen

```bash
docker pull erickyamilrc/shipment-tracker-api:latest
```

### 2. Ejecutar la API con MySQL en Docker Compose

```bash
docker compose up -d
```

La aplicación no debe conectarse a `localhost`, sino al servicio `mysql` usando el puerto interno de MySQL:

```env
DATABASE_URL=mysql://root:secret@mysql:3306/shipments
```

Al arrancar:

- Docker Compose levanta los servicios `api` y `mysql`
- La API usa la imagen publicada del proyecto
- La aplicación se conecta a MySQL mediante la red interna de Docker

La API queda disponible en:

```text
http://127.0.0.1:8000
```


---

## Endpoints disponibles

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | `/status/{tracking_id}` | Obtiene el estado actual del paquete. |
| GET | `/location/{tracking_id}` | Devuelve la ubicación actual del envío. |
| GET | `/shipment/{id}/history` | Lista cronológicamente los puntos de control del paquete. |
| GET | `/shipment/{id}/dwell-time` | Calcula el tiempo que el paquete ha permanecido inmóvil en la ubicación actual. |

### Ejemplo de respuesta JSON: `/status/{tracking_id}`

```json
{
  "tracking_id": "DHL-123",
  "status": "En transito"
}
```

### Ejemplo de respuesta JSON: `/location/{tracking_id}`

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
