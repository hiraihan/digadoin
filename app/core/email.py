from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "",
    MAIL_PASSWORD=settings.MAIL_PASSWORD or "",
    MAIL_FROM=settings.MAIL_FROM or "noreply@digadoin.com",
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER or "smtp.gmail.com",
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


def get_password_reset_template(reset_link: str, user_name: str) -> str:
    """Generate HTML email template for password reset"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0A0A0A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #111111; border-radius: 16px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px 40px; text-align: center;">
                                <div style="display: inline-flex; align-items: center; gap: 12px;">
                                    <div style="width: 40px; height: 40px; background-color: #ffffff; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; color: #000000;">D</div>
                                    <span style="font-size: 24px; font-weight: bold; color: #ffffff;">digado.in</span>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 20px 40px 40px 40px;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0 0 16px 0; text-align: center;">Reset Your Password</h1>
                                <p style="color: #a0a0a0; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0; text-align: center;">
                                    Hi {user_name},<br><br>
                                    We received a request to reset your password. Click the button below to create a new password.
                                </p>
                                
                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td align="center" style="padding: 24px 0;">
                                            <a href="{reset_link}" style="display: inline-block; padding: 16px 32px; background-color: #ffffff; color: #000000; text-decoration: none; font-weight: bold; font-size: 16px; border-radius: 12px;">
                                                Reset Password
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 24px 0 0 0; text-align: center;">
                                    This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                                </p>
                                
                                <hr style="border: none; border-top: 1px solid #222222; margin: 32px 0;">
                                
                                <p style="color: #666666; font-size: 12px; line-height: 1.6; margin: 0; text-align: center;">
                                    If the button doesn't work, copy and paste this link into your browser:<br>
                                    <a href="{reset_link}" style="color: #3b82f6; word-break: break-all;">{reset_link}</a>
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 20px 40px; background-color: #0A0A0A; text-align: center;">
                                <p style="color: #666666; font-size: 12px; margin: 0;">
                                    © 2026 Digadoin. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


async def send_password_reset_email(email: EmailStr, reset_token: str, user_name: str):
    """
    Send password reset email to user.
    
    Args:
        email: User's email address
        reset_token: The password reset token
        user_name: User's display name
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    html_content = get_password_reset_template(reset_link, user_name)
    
    message = MessageSchema(
        subject="Reset Your Password - Digadoin",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)


def get_email_verification_template(verify_link: str, user_name: str) -> str:
    """Generate HTML email template for email verification"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0A0A0A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #111111; border-radius: 16px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px 40px; text-align: center;">
                                <div style="display: inline-flex; align-items: center; gap: 12px;">
                                    <div style="width: 40px; height: 40px; background-color: #ffffff; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; color: #000000;">D</div>
                                    <span style="font-size: 24px; font-weight: bold; color: #ffffff;">digado.in</span>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 20px 40px 40px 40px;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0 0 16px 0; text-align: center;">Welcome to Digadoin! 🎉</h1>
                                <p style="color: #a0a0a0; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0; text-align: center;">
                                    Hi {user_name},<br><br>
                                    Thanks for signing up! Please verify your email address to get started.
                                </p>
                                
                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td align="center" style="padding: 24px 0;">
                                            <a href="{verify_link}" style="display: inline-block; padding: 16px 32px; background-color: #22c55e; color: #ffffff; text-decoration: none; font-weight: bold; font-size: 16px; border-radius: 12px;">
                                                Verify Email Address
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 24px 0 0 0; text-align: center;">
                                    This link will expire in 24 hours. If you didn't create an account, please ignore this email.
                                </p>
                                
                                <hr style="border: none; border-top: 1px solid #222222; margin: 32px 0;">
                                
                                <p style="color: #666666; font-size: 12px; line-height: 1.6; margin: 0; text-align: center;">
                                    If the button doesn't work, copy and paste this link into your browser:<br>
                                    <a href="{verify_link}" style="color: #22c55e; word-break: break-all;">{verify_link}</a>
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 20px 40px; background-color: #0A0A0A; text-align: center;">
                                <p style="color: #666666; font-size: 12px; margin: 0;">
                                    © 2026 Digadoin. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


async def send_verification_email(email: EmailStr, verification_token: str, user_name: str):
    """
    Send email verification email to newly registered user.
    
    Args:
        email: User's email address
        verification_token: The email verification token
        user_name: User's display name
    """
    verify_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    html_content = get_email_verification_template(verify_link, user_name)
    
    message = MessageSchema(
        subject="Verify Your Email - Welcome to Digadoin!",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

