import logging
import smtplib
from config.settings import Settings
from utils.helpers import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, host=None, port=None, user=None, password=None):
        self.notifications = []
        self.email_host = host if host is not None else Settings.SMTP_HOST
        self.email_port = port if port is not None else Settings.SMTP_PORT
        self.email_user = user if user is not None else Settings.SMTP_USER
        self.email_password = password if password is not None else Settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not self.email_user or not self.email_password:
            logger.warning("SMTP não configurado; e-mail para %s não enviado.", to)
            return False
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail(self.email_user, to, message)
            logger.info("Email enviado para %s", to)
            return True
        except smtplib.SMTPException as exc:
            logger.error("Erro ao enviar email: %s", exc)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append(
            {
                "type": "task_assigned",
                "user_id": user.id,
                "task_id": task.id,
                "timestamp": utc_now(),
            }
        )

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [item for item in self.notifications if item["user_id"] == user_id]
