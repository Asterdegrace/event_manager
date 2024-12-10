from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .db_connection import notifications_collection, users_collection,events_collection

def send_email(to_email, subject, body):
    from_email = "EMAIL" 
    password = "EMAIL_PASSWORD"  

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_notifications_and_send_email():
    current_time = datetime.now()
    rounded_to_minute = current_time.replace(second=0, microsecond=0)
    notifications = notifications_collection.find({"notify_at": {"$lte": rounded_to_minute}})
    
    for notification in notifications:
        user = users_collection.find_one({"_id": notification["user_id"]})
        if user:
            event = events_collection.find_one({"_id": notification["event_id"]})
            if event:
                subject = f"Event Reminder: {event['name']}"
                body = f"Hello {user['name']},\n\nYou have an upcoming event: {event['name']} on {event['date']}.\n\nDon't forget!"
                send_email(user['email'], subject, body)
                notifications_collection.delete_one({"_id": notification["_id"]})

scheduler = BackgroundScheduler()
scheduler.add_job(check_notifications_and_send_email, 'interval', minutes=1)
scheduler.start()

try:
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
