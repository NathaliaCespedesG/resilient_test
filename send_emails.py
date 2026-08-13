import smtplib
from email.message import EmailMessage

# University SMTP server details
smtp_server = 'smtp.cc.ic.ac.uk'
smtp_port = 25  # Port for TLS
email_address = 'ncespede@ic.ac.uk'  # Replace with your university email address
email_password = 'NaAZLGCs1026'             # Replace with your email password

# Function to send an email
def send_email(to_email, subject, body):
    # Set up the email message
    msg = EmailMessage()
    msg['From'] = email_address
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)
    
    # Connect to the SMTP server and send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Start TLS encryption
            server.login(email_address, email_password)  # Authenticate
            server.send_message(msg)
            print(f'Email sent to {to_email}')
    except Exception as e:
        print(f'Failed to send email to {to_email}: {e}')

# Example usage
send_email('nathalia.cespedes@hotmail.es', 'Test Subject', 'Hello, this is a test email sent from Python!')
