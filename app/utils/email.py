from typing import Optional, TypedDict
from fastapi_mail import (
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
    ConnectionConfig,
)
from fastapi.templating import Jinja2Templates

from app.core.config import settings

templates = Jinja2Templates("templates")

conf = ConnectionConfig(
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
)


async def send_email(
    recipients: list[NameEmail],
    subject: str,
    plain_text: Optional[str],
    template: Optional[str],
    success_message: Optional[str],
):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=template if template else plain_text,
        subtype=MessageType.html if template else MessageType.plain,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": success_message if success_message else "Email has been sent"}


class User(TypedDict):
    name: str
    email: NameEmail


async def send_welcome_email(user: User, login_url: str):
    template = templates.env.get_template("email/create_account.html")
    html_content = template.render(
        user_name=user.get("name"),
        user_email=user.get("email"),
        login_url=login_url,
    )
    await send_email(
        recipients=[user["email"]],
        subject="Welcome to  AI Vacation Planner",
        plain_text=None,
        template=html_content,
        success_message="Welcome message  sent succesffully",
    )
