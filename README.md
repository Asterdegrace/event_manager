# Flask Event Management Application

This is a Flask-based web application designed for event management with user authentication and notifications. It allows users to register, log in, create events, set notifications, and manage event participants.

## Features

- **User Authentication**: Users can register, log in, and log out using JWT (JSON Web Tokens).
- **Event Management**: Users can create and manage events, invite participants, and update event details.
- **Notifications**: Users can set reminders for events, which are sent as notifications.
- **Roles**: Users can have different roles (admin/participant) within events, with the ability to update roles and remove users.

## Setup Instructions
- install all the requirements 

### Installation

1. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure MongoDB**:
    Ensure you have a MongoDB instance running. The application uses MongoDB collections for storing events and notifications.

4. **Run the application**:
    ```bash
    python app.py
    ```

    The application will be available at `http://localhost:5000`.

## Routes Overview

### Authentication & User Management

- **GET `/login`**: Display the login page.
- **POST `/login`**: Authenticate the user.
- **GET `/registration`**: Display the registration page.
- **POST `/registration`**: Register a new user.
- **POST `/logout`**: Log out the user.

### Event Management

- **GET `/`**: Display the main menu for logged-in users.
- **GET `/create_event`**: Display the event creation page.
- **POST `/create_event/post`**: Create a new event with a list of participants.
- **GET `/my_events`**: Display a list of events the user is participating in.
- **GET `/my_events/<event_id>`**: View details of a specific event.
- **PATCH `/my_events/<event_id>/post`**: Update event details.
- **POST `/my_events/<event_id>/post`**: Add or update participants in the event.

### Notifications

- **GET `/my_notifications`**: View the list of notifications for the user.
- **POST `/my_notifications_post`**: Delete notifications.
- **DELETE `/find_public_event`**: Remove an event from the public list (TODO).

### Error Handling

- **400 Bad Request**: Returned when the request is malformed or missing required parameters.
- **404 Not Found**: Returned when a resource is not found (e.g., event not found).
- **401 Unauthorized**: Returned when the user is not authenticated or the token is invalid/expired.

## JWT Authentication

The application uses JWT for authenticating users. When a user logs in, a JWT token is generated and stored in the browser cookies. The token is required for accessing protected routes.

- **JWT Secret Key**: The secret key used to sign JWT tokens is configured in `app.config["JWT_SECRET_KEY"]`.
- **Token Expiry**: The token expires in 8 hours.

## Real-Time Features

- **WebSockets (SocketIO)**: Used to provide real-time updates for events and notifications.

## Dependencies

- Flask
- Flask-SocketIO
- Flask-JWT-Extended
- Flask-Cors
- Python-dotenv
- pymongo (for MongoDB integration)

## Project Structure

- `application.py`: The main application file containing all routes and logic.
- `src/Classes/`: Contains the classes `User`, `Event`, and `Notification`.
- `src/auth.py`: Handles user authentication and event-related logic.
- `src/db_connection.py`: Contains database connection logic and collections setup.

## Troubleshooting

- **Token Expiration**: If your token expires, you will need to log in again.
- **Missing Dependencies**: Make sure all required packages are installed using `pip install -r requirements.txt`.
p.s. not all the notification fitures are added and project needs implementation of apscheduler, smtplib and email.mime. for sending notifications via email
Additional: cors
