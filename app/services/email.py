import resend, os
from dotenv import load_dotenv
from pydantic import HttpUrl

load_dotenv()
try:
    RESEND_KEY = os.environ["RESEND_API_KEY"]
    resend.api_key = RESEND_KEY
except KeyError:
    raise RuntimeError("RESEND_API_KEY is missing")

def send_verify_email(email_to: str, verification_token: str):
    try:
        resend.Emails.send({
            "from": "Rambolt <noreply@contact.rambolt.my.id>",
            "to": email_to,
            "subject": "Verify Your BookMarker Account",
            "html": f"""
                <h1>Welcome to Bookmarker!</h1>
                <p>Please use the following token to verify your account:</p>
                <h3><strong>{verification_token}</strong></h3>
                <p>The code is valid for only <strong>20 minutes</strong></p>
                <br>
                <br>
                <p>Regards,</p>
                <p>Bookmarker Teams</p>
            """
        })
    except Exception as e:
        print(f"Failed. {email_to}. Error: {e}")

def send_forgot_password(email_to: str, token: str):
    try:
        resend.Emails.send({
            "from": "Rambolt <noreply@contact.rambolt.my.id>",
            "to": email_to,
            "subject": "Reset Your Password Account",
            "html": f"""
                <h1>You requested to reset password!</h1>
                <p>Please use the following link to reset your password:</p>
                <a href="http://127.0.0.1:8000/auth/reset-password?token={token}">Click here to reset password</a>
                <p>The code is valid for only <strong>20 minutes</strong></p>
                <br>
                <br>
                <p>Regards,</p>
                <p>Bookmarker Teams</p>
            """
        })
    except Exception as e:
        print(f"Failed. {email_to}. Error: {e}")