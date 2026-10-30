import resend, os
from dotenv import load_dotenv
from pydantic import HttpUrl

load_dotenv()
try:
    RESEND_KEY = os.environ["RESEND_API_KEY"]
    resend.api_key = RESEND_KEY
except KeyError:
    raise RuntimeError("RESEND_API_KEY is missing")

def send_email(email_to: str):
    try:
        resend.Emails.send({
            "from": "Sender",
            "to": email_to,
            "subject": "<Choose Your subject>",
            "html": f"""
                <h1>Email works!</h1>
            """
        })
    except Exception as e:
        print(f"Failed. {email_to}. Error: {e}")

