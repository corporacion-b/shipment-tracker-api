from html import escape

import httpx

from src.core.config import settings


class EmailDeliveryError(RuntimeError):
    pass


class BrevoEmailService:
    endpoint = "https://api.brevo.com/v3/smtp/email"

    def send_verification_email(self, email: str, verification_url: str) -> None:
        if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
            raise EmailDeliveryError("Brevo no esta configurado.")

        safe_url = escape(verification_url, quote=True)
        payload = {
            "sender": {
                "email": settings.BREVO_SENDER_EMAIL,
                "name": settings.BREVO_SENDER_NAME,
            },
            "to": [{"email": email}],
            "subject": "Verifica tu correo en Shipment Tracker",
            "htmlContent": f"""
                <html>
                  <body>
                    <p>Hola,</p>
                    <p>Confirma tu correo para activar tu cuenta de Shipment Tracker.</p>
                    <p>
                      <a href="{safe_url}">Verificar mi correo</a>
                    </p>
                    <p>Si no creaste esta cuenta, puedes ignorar este mensaje.</p>
                  </body>
                </html>
            """,
            "textContent": (
                "Confirma tu correo para activar tu cuenta de Shipment Tracker: "
                f"{verification_url}"
            ),
        }
        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        }

        try:
            response = httpx.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmailDeliveryError("No se pudo enviar el correo de verificacion.") from exc
