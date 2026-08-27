import smtplib
import socket
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Gmail SMTP Configuration
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "campusinfohub@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "kziv svff pyyz uvsr").replace(" ", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Fallback IPv4 addresses for Gmail SMTP servers if local DNS resolution fails
GMAIL_FALLBACK_IPS = ["142.250.141.108", "142.250.141.109", "74.125.140.108", "192.178.211.108"]


def _try_send_smtp(target_host: str, port: int, to_email: str, msg_str: str, use_ssl: bool = False) -> bool:
    """Helper to attempt sending message over STARTTLS (port 587) or SSL (port 465)."""
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(target_host, port, timeout=10)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
        else:
            server = smtplib.SMTP(target_host, port, timeout=10)
            server.ehlo("smtp.gmail.com")
            server.starttls()
            server.ehlo("smtp.gmail.com")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)

        server.sendmail(SMTP_EMAIL, [to_email], msg_str)
        server.quit()
        return True
    except Exception as e:
        logger.debug(f"SMTP attempt via {target_host}:{port} (SSL={use_ssl}) failed: {e}")
        return False


def _connect_and_send_smtp(to_email: str, msg_str: str) -> bool:
    """Sends email using domain resolution first, falling back to static IPv4 addresses if DNS fails."""
    # 1. Attempt using configured SMTP_HOST (hostname) via 587 (STARTTLS) then 465 (SSL)
    if _try_send_smtp(SMTP_HOST, SMTP_PORT, to_email, msg_str, use_ssl=False):
        return True

    if _try_send_smtp(SMTP_HOST, 465, to_email, msg_str, use_ssl=True):
        return True

    # 2. If hostname lookup/connection fails (e.g. DNS gaierror Errno 11001), try fallback Gmail IPv4 addresses
    for ip in GMAIL_FALLBACK_IPS:
        if _try_send_smtp(ip, 587, to_email, msg_str, use_ssl=False):
            logger.info(f"Successfully delivered email via Gmail fallback IP {ip}")
            return True
        if _try_send_smtp(ip, 465, to_email, msg_str, use_ssl=True):
            logger.info(f"Successfully delivered email via Gmail fallback SSL IP {ip}")
            return True

    return False


def send_otp_email(to_email: str, otp: str, purpose: str = "PASSWORD_RESET") -> bool:
    """
    Sends a 6-digit OTP code to the recipient via Gmail SMTP.
    Supports purpose="EMAIL_VERIFICATION" or purpose="PASSWORD_RESET".
    Returns True if sent successfully, False otherwise.
    """
    try:
        norm_purpose = (purpose or "").strip().upper()
        is_verification = (norm_purpose == "EMAIL_VERIFICATION")
        subject_title = "Email Verification OTP" if is_verification else "Password Reset OTP"
        card_title = "Verify Your Email Address" if is_verification else "Password Reset Code"
        lead_text = (
            "Welcome to Campus InfoHub! Please verify your email address to activate your account by entering the 6-digit OTP code below:"
            if is_verification
            else "We received a request to reset the password for your account. Please use the following 6-digit OTP to proceed:"
        )

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[{otp}] {subject_title} - Campus InfoHub"
        msg['From'] = f"Campus InfoHub <{SMTP_EMAIL}>"
        msg['To'] = to_email

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #334155; }}
            .card {{ max-width: 480px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); }}
            .logo {{ font-size: 20px; font-weight: bold; color: #d97706; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; text-align: center; }}
            .title {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px; text-align: center; }}
            .text {{ font-size: 14px; color: #64748b; line-height: 1.6; text-align: center; margin-bottom: 24px; }}
            .otp-box {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #b45309; text-align: center; margin: 24px 0; padding: 18px; background: #fef3c7; border: 2px dashed #f59e0b; border-radius: 14px; font-family: monospace; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 32px; border-top: 1px solid #f1f5f9; pt-16px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🎓 Campus InfoHub</div>
            <div class="title">{card_title}</div>
            <div class="text">{lead_text}</div>
            
            <div class="otp-box">{otp}</div>
            
            <div class="text" style="font-size: 13px;">
              ⏱️ This code will expire in <strong>5 minutes</strong>.<br/>
              🔒 If you did not request this, please ignore this email.
            </div>

            <div class="footer">
              This is an automated security message. Please do not reply to this email.<br/>
              &copy; Campus InfoHub Security Team
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Log to server console
        print(f"\n==========================================")
        print(f"[{norm_purpose} OTP GENERATED] Email: {to_email} | OTP: {otp}")
        print(f"==========================================\n")

        success = _connect_and_send_smtp(to_email, msg.as_string())
        if success:
            logger.info(f"OTP ({purpose}) email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send OTP ({purpose}) email to {to_email} across all endpoints and fallbacks.")
            return False
    except Exception as e:
        logger.error(f"Error preparing OTP ({purpose}) email for {to_email}: {e}")
        return False
