from ..db_connection import events_collection, notifications_collection, users_collection
from bson import ObjectId
from datetime import datetime, timedelta


def validate_remind_before(remind_before, event_date):
    """Validate the remind_before time and ensure it's in the future."""
    if not isinstance(remind_before, timedelta):
        raise ValueError("Reminder must be a timedelta object.")

    if event_date - remind_before <= datetime.now():
        raise Exception("Reminder time must be in the future and before the event date.")
    
    return remind_before


class Notification:
    def __init__(self, event_id, user_id, remind_before):
        event = events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise Exception("Event not found.")
        
        event_date = event['date']
        if not event_date:
            raise Exception("Event date is not set.")
        
        self.remind_before = validate_remind_before(remind_before, event_date)
        
        self.event_id = ObjectId(event_id)
        self.user_id = ObjectId(user_id)
        self.notify_at = event['date'] - self.remind_before
    
    def create_notification(self):
        notification_data = {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "remind_before": self.remind_before.total_seconds(),  # Convert to seconds
            "notify_at": self.notify_at
        }
        result = notifications_collection.insert_one(notification_data)
        if result.inserted_id:
            print(f"Notification created successfully with ID: {result.inserted_id}")
            return(result.inserted_id)
        else:
            raise Exception("Failed to create notification.")
    
    def update_notification(self, notification_id, remind_before):
        try:
            notification_object_id = ObjectId(notification_id)
        except Exception:
            raise Exception("Invalid notification ID format.")
        
        notification = notifications_collection.find_one({"_id": notification_object_id})
        if not notification:
            raise Exception("Notification not found.")
        
        event = events_collection.find_one({"_id": notification["event_id"]})
        if not event:
            raise Exception("Related event not found.")
        
        try:
            remind_before_val = validate_remind_before(remind_before, event["date"])
        except ValueError as e:
            raise e
        
        notify_at = event['date'] - remind_before_val
        
        result = notifications_collection.update_one(
            {"_id": notification_object_id},
            {
                "$set": {
                    "remind_before": remind_before_val.total_seconds(),  # Convert to seconds
                    "notify_at": notify_at
                }
            }
        )
        
        if result.matched_count == 0:
            raise Exception("Notification not found.")
        elif result.modified_count == 0:
            print("No changes were made to the notification.")
        else:
            print("Notification updated successfully.")
    
    def delete_notification(self, notification_id):
        try:
            notification_object_id = ObjectId(notification_id)
        except Exception:
            raise Exception("Invalid notification ID format.")
        
        notification = notifications_collection.find_one({"_id": notification_object_id})
        if not notification:
            raise Exception("Notification not found.")
        
        event = events_collection.find_one({"_id": notification["event_id"]})
        if not event:
            raise Exception("Event not found.")
        
        user = users_collection.find_one({"_id": notification["user_id"]})
        if not event:
            raise Exception("Event not found.")
        
        notifications = event.get("notifications", [])
        if notification_object_id in notifications:
            notifications.remove(notification_object_id)
        
        events_collection.update_one(
            {"_id": event["_id"]},
            {"$set": {"notifications": notifications}}
        )

        notifications = user.get("notifications", [])
        for notification in notifications:
            if notification["notification_id"] == notification_object_id:
                notifications.remove(notification)
        
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"notifications": notifications}}
        )

        result = notifications_collection.delete_one({"_id": notification_object_id})
        if result.deleted_count == 0:
            raise Exception("Failed to delete notification.")
        else:
            print("Notification deleted successfully.")

