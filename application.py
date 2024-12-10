from flask import Flask, request, render_template, jsonify, redirect, url_for,make_response
from flask_jwt_extended import JWTManager, jwt_required, verify_jwt_in_request,get_jwt_identity
from datetime import timedelta
from flask_socketio import SocketIO
from src.Classes.User import User
from src.Classes.Event import Event
from src.Classes.Notification import Notification
from datetime import datetime
from src.auth import valid_login, log_the_user_in, check_user_instance, event_list, delete_user_from_event,update_user_role_in_event, return_user_id, add_notification,notification_list, delete_notification
from src.db_connection import events_collection,notifications_collection
from bson import ObjectId
from datetime import timedelta

app = Flask(__name__, template_folder='public/templates')
app.config["JWT_SECRET_KEY"] = "your_secret_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
jwt = JWTManager(app)
socketio = SocketIO(app)

                      
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return render_template('login.html', error="The token has expired")

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return render_template('login.html', error="Invalid token")

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return render_template('login.html', error="Unauthorized user.")

@app.errorhandler(400)
def bad_request(e):
    return {"error": "Bad request"}, 400

@app.errorhandler(404)
def not_found(e):
    return {"error": "Resource not found"}, 404


@app.before_request
def log_token():
    token = request.cookies.get('access_token_cookie')
    if token:
        print(f"Token found")
    else:
        print("No token found in cookies")

@app.get('/')
@jwt_required(optional=True)
def index():
    try:
        token = request.cookies.get('access_token_cookie')
        if not token:
            print("No token found in cookies.")
            return redirect(url_for('login'))

        verify_jwt_in_request()
        current_user = get_jwt_identity()

        if not current_user:
            print("User not found or token invalid.")
            return redirect(url_for('login'))

        return render_template('menu.html', current_user= current_user)

    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            if valid_login(email, password):
                response = log_the_user_in(email) 
                return response  
            else:
                error = 'Invalid email or password.'
        return render_template('login.html', error=error)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('login.html', error="An error occurred. Please try again.")

@app.route('/registration', methods=['POST', 'GET'])
def registration():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not check_user_instance(email):
            try:
                new_user = User(email=email, password=password)
                new_user.save_user_to_db()
                if valid_login(email, password):
                    response = log_the_user_in(email)
                    return response 
                response = redirect(url_for('index'))
                return response
            except Exception as e:
                print(f"Error: {e}")
                error = "Registration failed. Please try again."
        else:
            error = "User already exists"
    return render_template('registration.html', error=error)

@app.route('/logout', methods=['POST'])
def logout():
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('access_token_cookie') 
    return response


@app.route('/create_event', methods=['GET'])
@jwt_required(optional= True)
def create_event():
    try:
        token = request.cookies.get('access_token_cookie')
        if not token:
            print("No token found in cookies.")
            return jsonify({'error': 'No token found in cookies'}), 401 

        verify_jwt_in_request()
        current_user = get_jwt_identity()

        if not current_user:
            print("User not found or token invalid.")
            return jsonify({'error': 'User not found or token invalid'}), 401 

        error = None
        return render_template('create_event.html', current_user = current_user)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500
    


@app.route('/create_event/post', methods=['POST'])
def create_event_post():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided.'}), 400

            name = data.get('name')
            content = data.get('content')
            publicity = data.get('publicity')
            users = data.get('users', [])
            date = data.get('date')
            current_user = users[-1]
            user_set = set(users)
            user_list = []
            for user in user_set:
                if check_user_instance(user) and user != current_user:
                    user_list.append ({'email':user, 'role': False})
                elif check_user_instance(user) and user == current_user:
                    user_list.append ({'email':user, 'role': True})
            date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M")
            formatted_date = date_obj.strftime("%Y-%m-%d-%H:%M")
            try:
                new_event = Event(name = name, content= content, publicity= publicity, date = formatted_date, users = user_list)
                new_event.save_event_to_db()
                return jsonify({'message': 'Event created successfully.'}), 201
            except Exception as e:
                    print(f"Error: {e}")
                    error = "Registration failed. Please try again."
            return render_template('create_event.html', error=error)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500
    
@app.route('/my_events', methods=['GET'])
@jwt_required(optional=True)
def my_events():
    try:
        token = request.cookies.get('access_token_cookie')
        if not token:
            print("No token found in cookies.")
            return jsonify({'error': 'No token found in cookies'}), 401 

        verify_jwt_in_request()
        current_user = get_jwt_identity()

        if not current_user:
            print("User not found or token invalid.")
            return jsonify({'error': 'User not found or token invalid'}), 401 

        error = None
        events = event_list(current_user)
        for event in events:
            event["_id"] = str(event["_id"])
        return render_template('my_events.html', events =events, user = current_user)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/my_events/post', methods=["POST"])
def my_events_post():
    try:
        if request.method == 'POST': 
            data = request.json
            if not data:
                return jsonify({'error': 'Invalid JSON'}), 400
            notifications = data.get('notifications', [])
            user = data.get('user', None)
            for notification in notifications:
                event_id = notification['event_id']
                total_seconds = notification["reminder_time"] // 1000
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                remind_before_td = timedelta(days=days, hours=hours, minutes=minutes)
                add_notification(event_id, return_user_id(user), remind_before_td)
            return jsonify({'message': 'Notification successfully.'}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/my_notifications', methods=['GET'])
@jwt_required(optional=True)
def my_notifications():
    try:
        token = request.cookies.get('access_token_cookie')
        if not token:
            print("No token found in cookies.")
            return jsonify({'error': 'No token found in cookies'}), 401 

        verify_jwt_in_request()
        current_user = get_jwt_identity()

        if not current_user:
            print("User not found or token invalid.")
            return jsonify({'error': 'User not found or token invalid'}), 401 
        notifications = notification_list(current_user)
        return render_template('my_notifications.html', notifications = notifications)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/my_notifications_post', methods=['POST'])
def my_notifications_post():
    try:
        data = request.json
        if 'notifications' in data:
            for notification_id in data["notifications"]:
                delete_notification(notification_id)
        return {"message": "Notifications deleted successfully"}, 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500



@app.route('/find_public_event', methods=['POST', 'GET', 'DELETE'])
@jwt_required(optional=True)
def find_public_event():
    try:
        token = request.cookies.get('access_token_cookie')
        if not token:
            print("No token found in cookies.")
            return jsonify({'error': 'No token found in cookies'}), 401 

        verify_jwt_in_request()
        current_user = get_jwt_identity()

        if not current_user:
            print("User not found or token invalid.")
            return jsonify({'error': 'User not found or token invalid'}), 401 
        print(request.method)
        if request.method == 'GET':
            return render_template('create_event.html', current_user=current_user)
        if request.method == 'POST':
            print("trying to get json")
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500
    

@app.route('/my_events/<event_id>', methods=['GET'])
@jwt_required(optional=True)
def event_detail(event_id):
    try:
        token = request.cookies.get('access_token_cookie')
        if not token:
            print("No token found in cookies.")
            return jsonify({'error': 'No token found in cookies'}), 401 

        verify_jwt_in_request()
        current_user = get_jwt_identity()

        if not current_user:
            print("User not found or token invalid.")
            return jsonify({'error': 'User not found or token invalid'}), 401 
        
        
        if request.method == 'GET':
            event = events_collection.find_one({'_id': ObjectId(event_id)})
            if event:
                event['_id'] = str(event['_id'])
                del event['notifications']
                for user in event["users"]:
                    if user.get("email") == current_user:
                        print(event)
                        return render_template('my_events_details.html', event=event, current_user = user)
            return {"error": "Event not found"}, 404

    except Exception as e:
        return {"error": str(e)}, 400
    

@app.route('/my_events/<event_id>/post', methods=['PATCH', 'POST'])
def event_detail_post(event_id):
    try:
        if request.method == 'PATCH':
            data = request.json
            update_fields = {}
            print(data, 'dada')
            event = events_collection.find_one({'_id': ObjectId(event_id)})
            print(event)
            if 'name' in data:
                update_fields['name'] = data['name']
            if 'content' in data:
                update_fields['content'] = data['content']
            if 'date' in data:
                date_obj = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M")
                formatted_date = date_obj.strftime("%Y-%m-%d-%H:%M")
                update_fields['date'] = formatted_date
            if 'publicity' in data:
                update_fields['publicity'] = data['publicity']
            if 'users' in data:
                print('users', data['users'])
                update_fields['users'] = event['users'][:]
                for user in data['users']:
                    print(user)
                    print(data['users'])
                    if check_user_instance(user):
                        if ({'email': user, 'role': False}not in event['users']) and({'email': user, 'role': True} not in event['users']):
                            processed_user = {'email': user, 'role': False}
                            update_fields['users'].append(processed_user)
                
            if not update_fields:
                return {"error": "No valid fields provided for update"}, 400
            
            event_to_update = Event(name = 'name', content= 'content', publicity= True, date = "2024-12-17-00:27", users = [{'name':'Test', 'role': True}])
            event_to_update.update_event_in_db(event_id, update_fields)
            
            return {"message": "Event updated successfully"}, 200
        elif request.method == 'POST':
            data = request.json
            changes = data.get('changes', [])
            event = events_collection.find_one({'_id': ObjectId(event_id)})
            print(changes)
            if not event:
                return {"error": "Event not found"}, 404

            '''updated_users = event['users'][:]'''
            for change in changes:
                email = change['email']
                if change.get('delete'):            
                    delete_user_from_event(event_id, email)  # add user's session role
                elif change.get('changeRole'):
                    update_user_role_in_event(event_id,email )
                        
       
        return {"message": "Participants updated successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 400

@app.route('/notifications', methods=['GET', 'POST'])
def notification_menu():
    
    return render_template('notification_menu.html')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
