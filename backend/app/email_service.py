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


def send_alumni_approval_email(to_email: str, name: str) -> bool:
    """
    Sends an account activation notification to an approved alumni.
    Alumni can now log in using their registered email and the password they set during registration.
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎉 Alumni Registration Approved - Campus InfoHub"
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
            .badge {{ display: inline-block; background: #d1fae5; color: #065f46; font-weight: 700; font-size: 14px; border-radius: 50px; padding: 8px 20px; margin-bottom: 20px; }}
            .cta {{ display: block; background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; font-weight: 700; text-align: center; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-size: 15px; margin: 24px 0; }}
            .info-box {{ background: #fef3c7; border: 1px solid #fbbf24; border-radius: 12px; padding: 16px; margin: 16px 0; font-size: 13px; color: #78350f; text-align: left; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🎓 Campus InfoHub</div>
            <div style="text-align:center;"><span class="badge">✅ Account Approved</span></div>
            <div class="title">Welcome to the Alumni Portal, {name}!</div>
            <div class="text">
              Congratulations! Your alumni registration has been reviewed and <strong>approved</strong> by the administration.
              Your account is now active and you can log in to the Campus InfoHub Alumni Portal.
            </div>
            <div class="info-box">
              <strong>🔑 Your Login Credentials:</strong><br/>
              <strong>Email:</strong> {to_email}<br/>
              <strong>Password:</strong> The password you set during registration<br/><br/>
              Visit <strong>Campus InfoHub</strong> and click <em>Sign In</em> to access your alumni dashboard.
            </div>
            <a href="http://localhost:5173/login" class="cta">Sign In to Alumni Portal →</a>
            <div class="text" style="font-size:13px;">
              If you have any issues logging in, use the <strong>Forgot Password</strong> option on the login page.
            </div>
            <div class="footer">
              This is an automated message from Campus InfoHub. Please do not reply to this email.<br/>
              &copy; Campus InfoHub Administration
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        print(f"\n==========================================")
        print(f"[ALUMNI APPROVED] Sending approval email to: {to_email} ({name})")
        print(f"==========================================\n")

        success = _connect_and_send_smtp(to_email, msg.as_string())
        if success:
            logger.info(f"Alumni approval email sent successfully to {to_email}")
        else:
            logger.error(f"Failed to send alumni approval email to {to_email}")
        return success
    except Exception as e:
        logger.error(f"Error sending alumni approval email to {to_email}: {e}")
        return False


def send_alumni_rejection_email(to_email: str, name: str) -> bool:
    """
    Sends a rejection notification to an alumni whose registration was not approved.
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "📋 Alumni Registration Status - Campus InfoHub"
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
            .badge {{ display: inline-block; background: #fee2e2; color: #991b1b; font-weight: 700; font-size: 14px; border-radius: 50px; padding: 8px 20px; margin-bottom: 20px; }}
            .info-box {{ background: #fef2f2; border: 1px solid #fca5a5; border-radius: 12px; padding: 16px; margin: 16px 0; font-size: 13px; color: #7f1d1d; text-align: left; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🎓 Campus InfoHub</div>
            <div style="text-align:center;"><span class="badge">❌ Registration Not Approved</span></div>
            <div class="title">Registration Update, {name}</div>
            <div class="text">
              Thank you for registering on Campus InfoHub. After reviewing your submission,
              the administration was unable to approve your registration at this time.
            </div>
            <div class="info-box">
              <strong>📋 What this means:</strong><br/>
              Your alumni registration application has not been approved. This may be due to
              verification issues with the information submitted. Please contact the administration
              for further information.
            </div>
            <div class="text" style="font-size:13px;">
              If you believe this is an error, please contact the college administration directly
              with your enrollment number and supporting documents.
            </div>
            <div class="footer">
              This is an automated message from Campus InfoHub. Please do not reply to this email.<br/>
              &copy; Campus InfoHub Administration
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        print(f"\n==========================================")
        print(f"[ALUMNI REJECTED] Sending rejection email to: {to_email} ({name})")
        print(f"==========================================\n")

        success = _connect_and_send_smtp(to_email, msg.as_string())
        if success:
            logger.info(f"Alumni rejection email sent to {to_email}")
        else:
            logger.error(f"Failed to send alumni rejection email to {to_email}")
        return success
    except Exception as e:
        logger.error(f"Error sending alumni rejection email to {to_email}: {e}")
        return False


def send_alumni_registration_email(to_email: str, name: str) -> bool:
    """
    Sends a registration confirmation email to newly registered alumni.
    Informs them that their registration is pending admin approval.
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "📋 Alumni Registration Received - Campus InfoHub"
        msg['From'] = f"Campus InfoHub <{SMTP_EMAIL}>"
        msg['To'] = to_email

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #334155; }}
            .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; padding: 36px; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.07); }}
            .logo {{ font-size: 20px; font-weight: bold; color: #d97706; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; text-align: center; }}
            .title {{ font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 6px; text-align: center; }}
            .subtitle {{ font-size: 14px; color: #64748b; text-align: center; margin-bottom: 28px; line-height: 1.6; }}
            .badge {{ display: inline-block; background: #fef3c7; color: #92400e; font-weight: 700; font-size: 13px; border-radius: 50px; padding: 6px 18px; margin-bottom: 20px; border: 1px solid #fbbf24; }}
            .steps {{ background: #f8fafc; border-radius: 14px; padding: 20px 24px; margin-bottom: 24px; border: 1px solid #e2e8f0; }}
            .steps h4 {{ font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 14px 0; }}
            .step {{ margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #f59e0b; }}
            .step-text {{ font-size: 13px; color: #475569; line-height: 1.5; }}
            .step-text strong {{ color: #0f172a; }}
            .info-box {{ background: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px; padding: 16px 20px; margin: 20px 0; font-size: 13px; color: #78350f; line-height: 1.8; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 28px; border-top: 1px solid #f1f5f9; padding-top: 16px; line-height: 1.6; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🎓 Campus InfoHub</div>
            <div style="text-align:center; margin-bottom: 16px;">
              <span style="font-size: 48px;">📋</span><br/>
              <span class="badge">⏳ Pending Admin Approval</span>
            </div>
            <div class="title">Registration Received, {name}!</div>
            <div class="subtitle">
              Thank you for registering on the <strong>Campus InfoHub Alumni Portal</strong>.<br/>
              Your application has been successfully submitted and is now under review.
            </div>

            <div class="steps">
              <h4>📌 What happens next?</h4>
              <div class="step">
                <div class="step-text"><strong>Step 1 — Application Review:</strong> Our admin team will verify your submitted information and enrollment details.</div>
              </div>
              <div class="step">
                <div class="step-text"><strong>Step 2 — Approval Notification:</strong> You will receive an email at <strong>{to_email}</strong> once your account is approved.</div>
              </div>
              <div class="step">
                <div class="step-text"><strong>Step 3 — Access Granted:</strong> After approval, sign in using your registered email and the password you set during registration.</div>
              </div>
            </div>

            <div class="info-box">
              🔑 <strong>Registered Email:</strong> {to_email}<br/>
              🔒 <strong>Password:</strong> The one you set during registration<br/>
              📞 For queries, please contact the college administration directly.
            </div>

            <div class="footer">
              This is an automated message from Campus InfoHub. Please do not reply to this email.<br/>
              © Campus InfoHub Alumni Portal
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        print(f"\n==========================================")
        print(f"[ALUMNI REGISTERED] Sending confirmation email to: {to_email} ({name})")
        print(f"==========================================\n")

        success = _connect_and_send_smtp(to_email, msg.as_string())
        if success:
            logger.info(f"Alumni registration confirmation email sent to {to_email}")
        else:
            logger.error(f"Failed to send alumni registration confirmation email to {to_email}")
        return success
    except Exception as e:
        logger.error(f"Error sending alumni registration confirmation email to {to_email}: {e}")
        return False
