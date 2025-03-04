import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from turtle import st
from googletrans import Translator, LANGUAGES
import requests
import pyttsx3
from bs4 import BeautifulSoup

def get_supported_languages():
    # Get the supported languages from googletrans
    return list(LANGUAGES.values())

def translate_text(text, target_language):
    try:
        translator = Translator()
        # Use the language code for translation
        lang_code = [code for code, name in LANGUAGES.items() if name == target_language][0]
        translated = translator.translate(text, dest=lang_code)
        return translated.text
    except Exception as e:
        print(f"Error during translation: {e}")  # Debugging
        return "Translation failed."
    
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def send_email(sender_email, receiver_email, subject, body, attachment_paths=None):
    try:
        # Create a multipart message container
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Attach the email body as plain text
        message.attach(MIMEText(body, "plain"))

        # Attach files
        if attachment_paths:
            for path in attachment_paths:
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                message.attach(part)

        # Use a secure connection (TLS)
        with smtplib.SMTP("rohithkarthikeya05@gmail.com", 587) as server:  # Replace with your email provider's SMTP server
            server.starttls()
            # Login to the sender's email account (you may need to use an app password)
            # For Gmail, enable "Less secure app access" or use an app password:
            # https://myaccount.google.com/apppasswords
            password = st.text_input("Enter the password of Mail ID",type="password")# you should add this in the setting page.
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())


        return True  # Email sent successfully

    except Exception as e:
        print(f"Error sending email: {e}")  # Log the error
        return False  # Email sending failed