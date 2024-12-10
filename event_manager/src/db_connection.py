from pymongo import MongoClient

try:
    DB_URI = "mongodb+srv://AnnaEnkin:12345@cluster.kgo3b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
    DB_NAME = "event_management_database"

    client = MongoClient(DB_URI)
    db = client[DB_NAME]
    events_collection = db['events']
    users_collection = db['users']
    notifications_collection = db['notifications']

    print("Successfully connected to the database!")
    
except Exception as e:
    print(f"Failed to connect to the database: {e}")



__all__ = ['events_collection', 'users_collection', 'notifications_collection', 'client', 'db']
