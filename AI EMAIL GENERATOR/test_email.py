# test_email.py (Create this new file)
import smtplib
from email.mime.text import MIMEText

def send_test_email(sender, receiver, password):
    try:
        message = MIMEText("This is a test email from the simplified script.")
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = "Test Email"

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)  # Replace with your sender email and APP PASSWORD
            server.sendmail(sender, receiver, message.as_string())
        print("Test email sent successfully!")

    except Exception as e:
        print(f"Error sending test email: {e}")

if __name__ == "__main__":
    sender_email = "your_sender_email@gmail.com" #change to the respective one
    receiver_email = "recipient_email@example.com" # Change to any of your known email.
    app_password = "your_app_password"  #  App password!

    send_test_email(sender_email, receiver_email, app_password)