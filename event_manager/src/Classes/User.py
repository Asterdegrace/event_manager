from ..db_connection import users_collection, events_collection, notifications_collection
from bson import ObjectId
import re
import hashlib

def validate_email(email):
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if not re.match(email_regex, email):
        raise ValueError("Invalid email format. Please enter a valid email address.")
    return email

def hash_password(password):
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must be a string with at least 8 characters.")
    return hashlib.sha256(password.encode()).hexdigest()

class User:
    
    def __init__(self, email, password):
        try:
            if not isinstance(password, str) or len(password) < 8:
                raise ValueError("Password must be at least 8 characters long.")
            
            self.email = validate_email(email)
            self.password = hash_password(password)
            self.events = []
            self.notifications = []
        except Exception as e:
            raise Exception(f"Error during user initialization: {e}")

    def save_user_to_db(self):
        try:
            user_data = {
                "email": self.email,
                "password": self.password,
                "events": self.events
            }
            if not validate_email(self.email):
                raise Exception('Please write correct email')
            users_collection.insert_one(user_data)
            print("User created successfully.")
        except Exception as e:
            raise Exception(f"Error saving user to database: {e}")

    def update_user(self, user_id, updated_fields):
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            raise Exception("Invalid user ID format.")
        
        try:
            user = users_collection.find_one({"_id": user_object_id})
            if not user:
                raise Exception("User not found in the database.")
            
            if "email" in updated_fields:
                new_email = updated_fields["email"]
                if not isinstance(new_email, str) or "@" not in new_email or "." not in new_email:
                    raise ValueError("Email must be a valid email address.")
                
                for event_entry in user["events"]:
                    event_id = event_entry["event_id"]
                    event = events_collection.find_one({"_id": ObjectId(event_id)})
                    if not event:
                        continue
                    for event_user in event.get("users", []):
                        if event_user["email"] == self.email:
                            event_user["email"] = new_email
                    events_collection.update_one(
                        {"_id": ObjectId(event_id)},
                        {"$set": {"users": event["users"]}}
                    )

            if "password" in updated_fields:
                new_password = updated_fields["password"]
                if not isinstance(new_password, str) or len(new_password) < 8:
                    raise ValueError("Password must be at least 8 characters long.")
                updated_fields["password"] = hash_password(new_password)

            result = users_collection.update_one(
                {"_id": user_object_id},
                {"$set": updated_fields}
            )

            if result.matched_count == 0:
                raise Exception("User not found in the database.")
            elif result.modified_count == 0:
                print("No changes were made to the user.")
            else:
                print("User updated successfully.")
        except Exception as e:
            raise Exception(f"Error updating user: {e}")


    def delete_user(self, user_id):
        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            raise Exception("Invalid user ID format.")
        
        try:
            user = users_collection.find_one({"_id": user_object_id})
            if not user:
                raise Exception("User not found in the database.")
            
            for event_entry in user["events"]:
                try:
                    event_id = event_entry["event_id"]
                    event = events_collection.find_one({"_id": ObjectId(event_id)})
                    if not event:
                        continue
                    event_users = [
                        u for u in event.get("users", []) if str(u["user_id"]) != str(user_object_id)
                    ]
                    events_collection.update_one(
                        {"_id": ObjectId(event_id)},
                        {"$set": {"users": event_users}}
                    )
                except Exception as e:
                    print(f"Error removing user from event {event_entry['event_id']}: {e}")
            
            try:
                notifications_collection.delete_many({"user_id": user_object_id})
            except Exception as e:
                print(f"Error deleting notifications for user: {e}")
            
            result = users_collection.delete_one({"_id": user_object_id})
            if result.deleted_count == 0:
                raise Exception("Failed to delete user.")
            print("User and associated data deleted successfully.")
        except Exception as e:
            raise Exception(f"Error deleting user: {e}")
