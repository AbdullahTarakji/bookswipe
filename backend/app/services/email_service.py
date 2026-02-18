"""Email service abstraction with SMTP backend.

Provides a pluggable interface so the SMTP backend can be swapped
(e.g. for SendGrid, SES) without touching business logic.
"""

from __future__ import annotations

import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("bookswipe.email")


class EmailBackend(ABC):
    """Abstract interface for sending emails."""

    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> bool:
        """Send an email. Returns True on success."""
        ...


class SMTPBackend(EmailBackend):
    """SMTP-based email delivery."""

    def __init__(
        self,
        host: str = "",
        port: int = 587,
        user: str = "",
        password: str = "",
        from_email: str = "",
        use_tls: bool = True,
    ) -> None:
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.user = user or settings.smtp_user
        self.password = password or settings.smtp_password
        self.from_email = from_email or settings.from_email
        self.use_tls = use_tls

    def send(self, to: str, subject: str, html_body: str) -> bool:
        if not self.host:
            logger.warning("SMTP not configured — skipping email to %s", to)
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_email, [to], msg.as_string())
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to)
            return False


class ConsoleBackend(EmailBackend):
    """Prints emails to the log — useful for development."""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        logger.info("📧 [Console Email] To: %s | Subject: %s", to, subject)
        return True


# ── Module-level singleton ───────────────────────────────────

_backend: EmailBackend | None = None


def get_email_backend() -> EmailBackend:
    """Return the configured email backend singleton."""
    global _backend
    if _backend is None:
        if settings.smtp_host:
            _backend = SMTPBackend()
        else:
            _backend = ConsoleBackend()
    return _backend


def set_email_backend(backend: EmailBackend) -> None:
    """Override the email backend (for testing)."""
    global _backend
    _backend = backend


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email using the configured backend."""
    return get_email_backend().send(to, subject, html_body)
