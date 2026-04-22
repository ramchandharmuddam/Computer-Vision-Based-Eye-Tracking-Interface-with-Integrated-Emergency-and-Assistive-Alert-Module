# email_sender.py
import smtplib
from email.message import EmailMessage


def send_emergency_email():
    try:
        sender_email = "emergencyperson007@gmail.com"
        password = "mxedoscmriwahfwa"   # App password (no spaces)
        recipient_email = "Yachekrishnareddy@gmail.com"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        msg = EmailMessage()
        msg.set_content("""
        EMERGENCY ALERT!

        I'm in an emergency situation and need your help immediately.
        Please check on me as soon as possible.
        """)

        msg['Subject'] = '🚨 EMERGENCY ALERT - Need Assistance'
        msg['From'] = sender_email
        msg['To'] = recipient_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)

        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)