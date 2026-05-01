# DHL Shipment Tracker API

<p align="center">
  API de rastreo de envíos construida con FastAPI que consume DHL y persiste el estado actual en MySQL.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

---

## Propósito

`shipment-tracker-api` centraliza la consulta de un envío en un endpoint HTTP simple. Por ahora el flujo implementado es:

1. recibe un `tracking_id`
2. consulta la API de DHL
3. normaliza la respuesta
4. guarda o actualiza el estado actual en MySQL
5. devuelve una respuesta JSON estable al cliente

La persistencia se pensó para poder crecer luego hacia historial, ubicación, `dwell-time` y análisis de riesgo sin reescribir el flujo principal.

---

## Estado actual

El endpoint funcional hoy es:

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | `/status/{tracking_id}` | Consulta DHL, persiste el estado actual y devuelve `tracking_id`, `status` y `description`. |

Ejemplo de respuesta:

```json
{
  "tracking_id": "7777777770",
  "status": "TRANSIT",
  "description": "The shipment is in transit"
}
```

Errores esperados:

| Código | Descripción |
| --- | --- |
| `404` | DHL no encontró la guía consultada. |
| `422` | La estructura del JSON devuelto por DHL no tiene el formato esperado. |
| `500` | Error de configuración o conexión no controlado. |
| `504` | Timeout al consultar DHL. |

---

## Arquitectura implementada

La implementación actual para `/status/{tracking_id}` se separa en capas para poder añadir más endpoints sin duplicar lógica:

- `src/api/routes/tracking.py`: capa HTTP
- `src/services/tracking.py`: orquesta el caso de uso
- `src/services/dhl.py`: cliente hacia DHL
- `src/repositories/shipment_repository.py`: persistencia del estado actual
- `src/db/connection.py`: conexión e inicialización de esquema

Tablas creadas automáticamente al arrancar:

- `shipments`: estado actual persistido por `tracking_id`
- `tracking_events`: preparada para futuros endpoints de historial y eventos

---

## Estructura del proyecto

```text
shipment-tracker-api/
├── .github/
├── docs/
├── src/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## Requisitos previos

- Python 3.10 o superior
- `pip`
- Docker Desktop o Docker Engine con Compose
- credenciales válidas de DHL

---

## Variables de entorno

Copia `.env.example` a `.env` y ajusta las credenciales:

```bash
cp .env.example .env
```

Contenido esperado:

```env
PROJECT_NAME=Shipment Tracker API
DHL_API_KEY=your_dhl_api_key
DHL_API_SECRET=your_dhl_api_secret
DHL_BASE_URL=https://api-eu.dhl.com/track/shipments
DATABASE_URL=mysql://root:secret@localhost:3306/shipments
```

Notas:

- `DATABASE_URL` usa MySQL local corriendo en Docker y expuesto por el puerto `3306`.
- Si la API corre fuera de Docker y MySQL dentro de Docker, `localhost` es correcto.
- `DHL_API_SECRET` hoy se sigue leyendo desde configuración aunque la llamada actual a DHL usa solo `DHL_API_KEY`.

---

## Arranque local con MySQL en Docker

### 1. Levantar MySQL

Desde la raíz del proyecto:

```bash
docker compose up -d mysql
```

Esto crea un contenedor MySQL 8 con:

- host: `localhost`
- puerto: `3306`
- usuario: `root`
- contraseña: `secret`
- base de datos: `shipments`

Para confirmar que está saludable:

```bash
docker compose ps
docker compose logs mysql
```

### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 3. Arrancar la API

```bash
uvicorn src.main:src --reload
```

Al arrancar:

- la aplicación lee `.env`
- se conecta a MySQL usando `DATABASE_URL`
- crea las tablas mínimas si no existen

La API queda disponible en:

```text
http://127.0.0.1:8000
```

### 4. Probar el endpoint

```bash
curl http://127.0.0.1:8000/status/TU_TRACKING_REAL
```

Si DHL reconoce la guía:

- FastAPI devuelve `tracking_id`, `status` y `description`
- MySQL guarda o actualiza el registro en `shipments`

Si DHL no reconoce la guía verás algo como:

```json
{"detail":"Guía 'TU_TRACKING_REAL' no existe."}
```

En ese caso no habrá persistencia porque la consulta externa falló antes del guardado.

---

## Verificación de persistencia

### Opción 1: desde DBeaver

Conéctate a MySQL con estos datos:

- host: `localhost`
- port: `3306`
- database: `shipments`
- user: `root`
- password: `secret`

Consulta útil:

```sql
SELECT id, tracking_id, carrier, current_status, current_description, last_synced_at
FROM shipments
ORDER BY id DESC;
```

### Opción 2: desde el cliente MySQL dentro del contenedor

```bash
docker exec -it shipment-mysql mysql -uroot -psecret shipments
```

Luego:

```sql
SHOW TABLES;

SELECT id, tracking_id, carrier, current_status, current_description, last_synced_at
FROM shipments;
```

---

## Pruebas automatizadas

Ejecuta la suite con:

```bash
pytest -q
```

Las pruebas validan que `/status/{tracking_id}`:

- responde correctamente
- persiste el envío consultado
- actualiza el mismo envío sin duplicarlo

Importante:

- los tests usan una base SQLite aislada para no depender de MySQL local
- el entorno de desarrollo del equipo queda estandarizado con MySQL en Docker

---

## Docker Compose

El proyecto incluye [docker-compose.yml](/Users/enriquevido/Documents/UV/6to/Despliegue%20de%20software/proyecto/shipment-tracker-api/docker-compose.yml) para estandarizar la base de datos local.

Hoy el `compose` solo levanta MySQL. La API sigue ejecutándose desde `uvicorn` en la máquina local, lo cual simplifica depuración y desarrollo. Más adelante se puede añadir un servicio `api` al mismo `compose` sin cambiar el flujo de persistencia ya implementado.

---

## Notas para el equipo

- No editen tablas a mano como mecanismo principal de cambios de esquema.
- Mientras no exista Alembic, el esquema actual se crea automáticamente al arrancar.
- Si alguien cambia la estructura de tablas, debe coordinarlo con el equipo y reflejarlo en código y documentación.
- El siguiente paso natural para madurar esta base es introducir migraciones con Alembic.

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
