import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_addr = settings.EMAIL_FROM_ADDRESS or self.user

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    def _send(self, to: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        """Low-level SMTP send. Returns True on success, False on failure."""
        if not self.is_configured:
            logger.debug(f"Email not configured, skipping: {subject} → {to}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = to

            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html:
                msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_addr, [to], msg.as_string())

            logger.info(f"Email sent: {subject} → {to}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def _render(self, template: str, **kwargs) -> tuple[str, str]:
        """Render email template. Returns (plain, html)."""
        # Simple {{var}} substitution
        def replace(text):
            for k, v in kwargs.items():
                text = text.replace(f"{{{{{k}}}}}", str(v))
            return text

        plain = replace(template)
        html = template.replace("\n", "<br>")
        for k, v in kwargs.items():
            html = html.replace(f"{{{{{k}}}}}", f"<b>{v}</b>")
        return plain, html

    def send_welcome(self, email: str, username: str) -> bool:
        subject = "欢迎注册 TokenDancer"
        body, html = self._render(
            "欢迎 {{username}}！\n感谢您注册 TokenDancer。\n\n您可以登录后购买算力或兑换余额，开始使用 API 服务。",
            username=username,
        )
        return self._send(email, subject, body, html)

    def send_password_changed(self, email: str, username: str) -> bool:
        subject = "密码修改通知"
        body, html = self._render(
            "您好 {{username}}，\n\n您的账户密码已于北京时间 {{time}} 被修改。\n\n如果不是您本人操作，请立即联系我们。",
            username=username,
            time="刚刚",
        )
        return self._send(email, subject, body, html)

    def send_order_created(self, email: str, username: str, order_no: str, amount: str) -> bool:
        subject = f"订单已创建：{order_no}"
        body, html = self._render(
            "您好 {{username}}，\n\n您的订单 {{order_no}} 已创建，待支付金额：${{amount}}。\n\n请前往商城完成支付。",
            username=username,
            order_no=order_no,
            amount=amount,
        )
        return self._send(email, subject, body, html)

    def send_order_paid(self, email: str, username: str, order_no: str, db=None) -> bool:
        subject = f"订单支付成功：{order_no}"
        body, html = self._render(
            "您好 {{username}}，\n\n您的订单 {{order_no}} 已支付成功！\n\n权益已发放到您的账户，感谢购买！",
            username=username,
            order_no=order_no,
        )
        return self._send(email, subject, body, html)

    def send_redeem_success(self, email: str, username: str, code: str, amount: str) -> bool:
        subject = "兑换码兑换成功"
        body, html = self._render(
            "您好 {{username}}，\n\n兑换码 {{code}} 兑换成功，充值金额：${{amount}}。\n\n余额已到账，感谢使用！",
            username=username,
            code=code,
            amount=amount,
        )
        return self._send(email, subject, body, html)


email_service = EmailService()
