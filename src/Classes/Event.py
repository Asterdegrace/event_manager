from ..db_connection import events_collection, notifications_collection, users_collection
from bson import ObjectId
from datetime import datetime

class Event:
    def __init__(self, name, date, content, publicity, users):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Name must be a non-empty string.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content must be a non-empty string.")
        if not isinstance(publicity, bool):
            raise ValueError("Publicity must be a boolean value.")
        
        try:
            self.date = datetime.strptime(date, "%Y-%m-%d-%H:%M")
        except ValueError:
            raise ValueError("Date must be in the format 'YYYY-MM-DD-HH:MM'.")
        
        self.name = name
        self.content = content
        self.publicity = publicity
        self.users = users
    
    def save_event_to_db(self):
        event_data = {
            "name": self.name,
            "date": self.date,
            "content": self.content,
            "publicity": self.publicity,
            "users": self.users
        }
        events_collection.insert_one(event_data)
        for user in self.users:
            current_user = users_collection.find_one({"email": user['email']})
            if current_user:
                event_entry = {"event_id": event_data["_id"], "role": user['role']}
                users_collection.update_one(
                {"email": user["email"]},
                {"$push": {"events": event_entry}} 
                )
    def update_event_in_db(self, event_id, updated_fields):
        try:
            event_object_id = ObjectId(event_id)
        except Exception:
            raise Exception("Invalid event ID format.")
        
        result = events_collection.update_one(
            {"_id": event_object_id}, 
            {"$set": updated_fields}
        )
        
        if result.matched_count == 0:
            raise Exception("Event not found in the database.")
        elif result.modified_count == 0:
            print("No changes were made to the event.")
            return

        if "users" in updated_fields:
            for user in updated_fields["users"]:
                current_user = users_collection.find_one({"email": user["email"]})
                if ({"event_id": event_object_id, "role": False} not in current_user["events"]) and ({"event_id": event_object_id, "role": True} not in current_user["events"]):
                    current_user["events"].append({"event_id": event_object_id, "role": False})
                    users_collection.update_one(
                        {"email": user["email"]},
                        {"$set":{"events": current_user["events"]}}
                    )
            

        if "date" in updated_fields:
            try:
                new_date = datetime.strptime(updated_fields["date"], "%Y-%m-%d-%H:%M")
            except ValueError:
                raise ValueError("Date must be in the format 'YYYY-MM-DD-HH:MM'.")
            

            notifications = notifications_collection.find({"event_id": event_object_id})
            for notification in notifications:

                notify_at = new_date 
                if notify_at < datetime.now():
                    raise Exception("Notification notify_at cannot be in the past.")
                notifications_collection.update_one(
                    {"_id": notification["_id"]},
                    {"$set": {"notify_at": notify_at}}
                )
            print("Event and related notifications updated successfully.")
        

    def delete_event_from_db(self, event_id):
        try:
            event_object_id = ObjectId(event_id)
        except Exception:
            raise Exception("Invalid event ID format.")
        
        deleted_event = events_collection.find_one_and_delete({"_id": event_object_id})
        if not deleted_event:
            raise Exception("Event not found in the database.")
        
        result = notifications_collection.delete_many({"event_id": event_object_id})
        print(f"Event deleted successfully. {result.deleted_count} related notifications were also deleted.")
        
        try:
            users_collection.update_many(
                {"events.event_id": event_object_id},
                {"$pull": {"events": {"event_id": event_object_id}}}
            )
            print("Event removed from users' event lists.")
        except Exception as e:
            print(f"Error removing event from users: {e}")
        
        return deleted_event
    

    def add_user_to_event(self, event_id, publicity, creator_role, user_id, user_role=False):
        try:
            if not publicity and not creator_role:
                raise Exception("Only moderators can add users to non-public events.")

            event_object_id = ObjectId(event_id)
            event = events_collection.find_one({"_id": event_object_id})
            if not event:
                raise Exception("Event not found in the database.")

            if any(str(user["user_id"]) == str(user_id) for user in event.get("users", [])):
                raise Exception("User already exists in the event.")

            event_users = event.get("users", [])
            event_users.append({"user_id": user_id, "role": user_role})

            events_collection.update_one(
                {"_id": event_object_id},
                {"$set": {"users": event_users}}
            )

            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise Exception("User not found in the database.")
            
            user["events"].append({"event_id": event_object_id, "role": user_role})
            
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"events": user["events"]}}
            )

            print(f"User {user_id} added to the event successfully.")
        except Exception as e:
            raise Exception(f"Failed to add user to event: {e}")


    def remove_user_from_event(self, event_id, creator_role, user_email):
        try:
            if not creator_role:
                raise Exception("Only moderators can remove users from events.")

            event_object_id = ObjectId(event_id)
            event = events_collection.find_one({"_id": event_object_id})
            if not event:
                raise Exception("Event not found in the database.")
            
            user_to_remove = None
            for user in event.get("users", []):
                if str(user["email"]) == str(user_email):
                    user_to_remove = user
                    break
            print('user tr', user_to_remove)
            if not user_to_remove:
                raise Exception("User is not in the event.")

            event_users = event.get("users", [])
            users_to_save = []
            for event_user in event_users:
                if user_email != event_user["email"]:
                    users_to_save.append(event_user)

            deleted_user= users_collection.find_one({"email": user_email})
            user_events = deleted_user.get('events', [])
            events_of_user_to_save = []
            for user_event in user_events:
                if user_event['event_id'] != event_object_id:
                    events_of_user_to_save.append(user_event)

            events_collection.update_one(
                {"_id": event_object_id},
                {"$set": {"users": users_to_save}}
            )
            users_collection.update_one(
                {"email": user_email},
                {"$set": {"events": events_of_user_to_save}}
            )

            print(f"User {user_email} removed from the event successfully.")
        except Exception as e:
            raise Exception(f"Failed to remove user from event: {e}")

    def change_user_role_in_event(self, event_id, creator_role, user_email):
        try:
            print("in method")
            if not creator_role:
                raise Exception("Only moderators can remove users from events.")

            event_object_id = ObjectId(event_id)
            event = events_collection.find_one({"_id": event_object_id})
            if not event:
                raise Exception("Event not found in the database.")
            
            user_to_change = None
            for user in event.get("users", []):
                if str(user["email"]) == str(user_email):
                    user_to_change = user
                    break
            if not user_to_change:
                raise Exception("User is not in the event.")

            event_users = event.get("users", [])
            users_to_save = []
            for event_user in event_users:
                if user_email != event_user["email"]:
                    users_to_save.append(event_user)
                else:
                    role = not event_user['role']
                    print('event: ',event_user)
                    users_to_save.append({"email":event_user['email'], "role": not event_user['role']})
                    

            updated_user= users_collection.find_one({"email": user_email})
            user_events = updated_user.get('events', [])
            events_of_user_to_save = []
            for user_event in user_events:
                if user_event['event_id'] != event_object_id:
                    events_of_user_to_save.append(user_event)
                else:
                    print('user: ',not event_user['role'])
                    events_of_user_to_save.append({"event_id": event_object_id, "role": not user_event["role"]})

            events_collection.update_one(
                {"_id": event_object_id},
                {"$set": {"users": users_to_save}}
            )
            users_collection.update_one(
                {"email": user_email},
                {"$set": {"events": events_of_user_to_save}}
            )

            print(f"User {user_email} changed the role.")
        except Exception as e:
            raise Exception(f"Failed to remove user from event: {e}")

    
    def time_left(self):
        now = datetime.now()
        if self.date < now:
            return "The event has already occurred."
        delta = self.date - now
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return f"Time left: {days} days, {hours} hours, and {minutes} minutes."


    


