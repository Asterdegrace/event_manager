from .db_connection import users_collection, events_collection, notifications_collection
from .Classes.User import hash_password
from flask_jwt_extended import create_access_token,create_refresh_token
from .Classes.User import User
from .Classes.Event import Event
from .Classes.Notification import Notification
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask import make_response, redirect, url_for,request
from bson import ObjectId
from datetime import datetime, timedelta

def valid_login(email, password):

    user = users_collection.find_one({"email": email})
    if not user:
        raise Exception('There is no such email in the database')
    db_password = user['password']
    if db_password != hash_password(password): 
        raise Exception('Password is incorrect')
    return True


def log_the_user_in(email):
    token = create_access_token(identity=email)
    print(f"Generated token: {token}") 
    
    response = make_response(redirect(url_for('index')))
    response.set_cookie('access_token_cookie', token)
    return response

def check_user_instance(email):

    user_data = users_collection.find_one({"email": email})
    return bool(user_data)

def event_list(email):
    user_data = users_collection.find_one({"email": email})
    if user_data and "events" in user_data:
        events = []
        for event in user_data["events"]:
            event_id = event['event_id']
            role = event['role']
            event_data = events_collection.find_one({"_id": event_id})
            if event_data:
                participants = len(event_data['users'])
                event_push = {'_id': event_data['_id'], 'name': event_data['name'], 'date': event_data["date"], 'role': role, 'participants': participants}
                events.append(event_push)
        return events
    else:
        return None

def delete_user_from_event(event_id, email):
    print('delete_user_from_event')
    event_to_delete = Event(name = 'name', content= 'content', publicity= True, date = "2024-12-17-00:27", users = [{'name':'Test', 'role': True}])
    event_to_delete.remove_user_from_event(event_id, True, email)
   
def update_user_role_in_event(event_id, email):
    print('update_user_in_event')
    event_to_delete = Event(name = 'name', content= 'content', publicity= True, date = "2024-12-17-00:27", users = [{'name':'Test', 'role': True}])
    event_to_delete.change_user_role_in_event(event_id, True, email)
   
def return_user_id(email):
    user = users_collection.find_one({"email": email})
    return (str(user['_id']))
   
def add_notification(event_id, user_id, remind_before):
    notification = Notification(remind_before= remind_before, event_id= event_id, user_id = user_id)
    notification_id = notification.create_notification()
    notification = notifications_collection.find_one({"_id": notification_id})
    user_entry = {"notification_id": notification_id, "notify_at": notification["notify_at"], "event_id": event_id}
    users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"notifications": user_entry}} 
                )
    events_collection.update_one(
                {"_id": ObjectId(event_id)},
                {"$push": {"notifications": notification_id}} 
                )

def notification_list(email):
    user_data = users_collection.find_one({"email": email})
    if user_data and "notifications" in user_data:
        notifications = []
        for notification in user_data["notifications"]:
            notification_id = notification['notification_id']
            notification_data = notifications_collection.find_one({"_id": notification_id})
            if notification_data:
                event = events_collection.find_one({"_id": ObjectId(notification_data["event_id"])})
                notification_push = {'_id': notification_data['_id'], 'name': event['name'], 'date': notification_data["notify_at"], 'event_id': str(notification_data['event_id'])}
                notifications.append(notification_push)
        return notifications
    else:
        return None

def delete_notification(notification_id):
    notification = Notification(remind_before= datetime.timedelta(days=1, seconds=19845), event_id= '67547bcbc005d85e1f0eedde', user_id = '67547baec005d85e1f0eeddc')
    notification.delete_notification(notification_id) 

'''def notification_list(email):
    user_data = users_collection.find_one({"email": email})
    if user_data and "notifications" in user_data:
        notifications = []
        for notification in user_data["notifications"]:
            notification_id = notification['event_id']
            event_data = events_collection.find_one({"_id": event_id})
            if event_data:
                participants = len(event_data['users'])
                event_push = {'_id': event_data['_id'], 'name': event_data['name'], 'date': event_data["date"], 'role': role, 'participants': participants}
                events.append(event_push)
        return events
    else:
        return None


    Safely retrieves the current user from the JWT token in cookies.

try:
        # Fetch token from cookies
        token = request.cookies.get('access_token_cookie')
        print(f"Token from cookies: {token}")  # Log the token for debugging
        
        if not token:
            print("No token found in cookies")
            return None
        
        # Verify the token using Flask JWT extended's built-in function
        verify_jwt_in_request()  # This will automatically look in the cookies
        
        current_user = get_jwt_identity()  # Get the user identity from the token
        return current_user
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        return None'''

