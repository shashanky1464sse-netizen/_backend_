"""
Email service — uses standard SMTP mail delivery.

Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env to enable real email delivery.
If SMTP_HOST or SMTP_USER is missing, the OTP is printed to the terminal as a fallback.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def send_otp_email(to_email: str, otp: str, subject: str, title: str, instructions: str) -> bool:
    """
    Send a 6-digit OTP to *to_email* using SMTP.
    Falls back to terminal output if SMTP settings are not configured.
    """
    smtp_host = settings.smtp_host
    smtp_port = settings.smtp_port
    smtp_user = settings.smtp_user
    smtp_password = settings.smtp_password
    smtp_from = settings.smtp_from or smtp_user
    smtp_tls = settings.smtp_tls

    if not smtp_host or not smtp_user or not smtp_password:
        logger.warning("SMTP credentials not fully set — falling back to terminal display.")
        _fallback_terminal(to_email, otp, title)
        return True  # treat as success so registration still works

    sender_name = "Resume2Interview"
    sender_email = smtp_from

    html_body = f"""
    <html>
      <body style="font-family:Arial,sans-serif;color:#333;background:#f4f4f4;margin:0;padding:0">
        <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">
          <div style="background:#4F46E5;padding:28px 32px">
            <h1 style="margin:0;color:#fff;font-size:20px;font-weight:700">Resume2Interview</h1>
          </div>
          <div style="padding:32px">
            <h2 style="margin:0 0 12px;font-size:18px;color:#1a1a2e">{title}</h2>
            <p style="margin:0 0 24px;color:#555;line-height:1.6">{instructions}</p>
            <div style="background:#f8f7ff;border:2px dashed #4F46E5;border-radius:8px;padding:20px;text-align:center;margin-bottom:24px">
              <span style="font-size:32px;font-weight:800;letter-spacing:10px;color:#4F46E5">{otp}</span>
            </div>
            <p style="margin:0 0 8px;color:#888;font-size:13px">This code expires in <strong>15 minutes</strong>.</p>
            <p style="margin:0;color:#888;font-size:13px">If you did not request this, you can safely ignore this email.</p>
          </div>
          <div style="padding:16px 32px;background:#f9f9f9;border-top:1px solid #eee">
            <p style="margin:0;font-size:12px;color:#aaa">&copy; 2025 Resume2Interview &middot; Automated message, do not reply.</p>
          </div>
        </div>
      </body>
    </html>
    """

    plain_body = (
        f"{title}\n\n{instructions}\n\n"
        f"Your verification code: {otp}\n\n"
        f"This code expires in 15 minutes.\n"
        f"If you did not request this, ignore this email.\n\n"
        f"--- Resume2Interview Team"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email

    part1 = MIMEText(plain_body, "plain")
    part2 = MIMEText(html_body, "html")

    msg.attach(part1)
    msg.attach(part2)

    try:
        if smtp_tls:
            # Usually port 587 uses STARTTLS
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            # Port 465 uses SSL directly (SMTPS) or unencrypted 25
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        
        server.login(smtp_user, smtp_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"OTP email sent successfully to {to_email} via SMTP.")
        return True
    except smtplib.SMTPAuthenticationError as auth_exc:
        logger.error(f"Failed to authenticate with SMTP server. Check SMTP_USER and SMTP_PASSWORD: {auth_exc}")
        _fallback_terminal(to_email, otp, title)
        return False
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email} via SMTP: {exc}")
        _fallback_terminal(to_email, otp, title)
        return False


def _fallback_terminal(to_email: str, otp: str, title: str) -> None:
    print("\n" + "=" * 50)
    print(f" {title.upper()} (FALLBACK — no email sent)")
    print(f" To:  {to_email}")
    print(f" OTP: {otp}")
    print("=" * 50 + "\n")
