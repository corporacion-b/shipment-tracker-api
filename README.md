# shipment-tracker-api

<p align="center">
  API de rastreo de envíos construida con FastAPI que consume la DHL API.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Pytest-Tests-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

API principal del sistema Shipment Tracker. Consulte [corporacion-b/.github](https://github.com/corporacion-b/.github) para la descripción completa del proyecto y las instrucciones de ejecución con Docker Compose.

---

## Requisitos previos

- Docker y Docker Compose
- Los tres repositorios clonados en la carpeta raíz del proyecto (ver [corporacion-b/.github](https://github.com/corporacion-b/.github))

---

## Ejecución

Este servicio se levanta junto con el resto del sistema desde la carpeta raíz del proyecto:

```bash
cp .env.example .env
docker compose up --build
```

Las variables de entorno se configuran en el `.env` de la raíz. La API queda disponible en `http://localhost:8000`.

---

## Endpoints

**Auth**

| Método | Endpoint | Descripción |
| --- | --- | --- |
| POST | `/auth/register` | Registrar usuario |
| POST | `/auth/login` | Iniciar sesión |
| POST | `/auth/verify-email` | Verificar correo |
| POST | `/auth/resend-verification` | Reenviar verificación de correo |
| GET | `/auth/me` | Obtener usuario autenticado |

**Shipments**

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | `/shipments` | Listar pedidos del usuario autenticado |
| GET | `/shipments/{tracking_id}` | Obtener detalle de un pedido |
| DELETE | `/shipments/{tracking_id}` | Borrar un pedido |
| POST | `/shipments/{tracking_id}/refresh` | Consultar DHL y actualizar un pedido |

**Tracking**

| Método | Endpoint | Descripción |
| --- | --- | --- |
| GET | `/status/{tracking_id}` | Estado actual del paquete |
| GET | `/location/{tracking_id}` | Ubicación actual del envío |
| GET | `/history/{tracking_id}` | Historial de eventos |
| GET | `/dwell-time/{tracking_id}` | Tiempo inmóvil en ubicación actual |
| GET | `/full-tracking/{tracking_id}` | Respuesta completa sin filtrar de DHL |

### Manejo de errores

| Código | Descripción |
| --- | --- |
| `400` | Formato de `id` inválido o parámetros faltantes |
| `401/403` | Fallo en autenticación o permisos insuficientes |
| `404` | Número de guía no encontrado |
| `429` | Límite de peticiones excedido |
| `500` | Error genérico del servidor |
| `502` | Respuesta inválida de la API DHL |
| `503` | API DHL no disponible |

Documentación automática: `http://localhost:8000/docs`

---

## Pruebas

```bash
pytest
```
