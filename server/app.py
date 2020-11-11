# from flask import Flask, render_template, session
# from flask_socketio import SocketIO, send, emit, join_room, leave_room
#
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app)
#
# # @app.route('/login')
# # def login():
# #     check password - assuming thats fine
# #     session['user'] = database.get("username")
#
# @app.route('/')
# def startup():
#     return """
#      <!DOCTYPE html>
#     <script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/2.2.0/socket.io.js" integrity="sha256-yr4fRk/GU1ehYJPAs8P4JlTgu0Hdsp4ZKrx8bDEDC3I=" crossorigin="anonymous"></script>
# <script type="text/javascript" charset="utf-8">
#     var socket = io();
#     socket.on('connect', function() {
#         socket.emit('join', {username: 'You\\'re fucked''});
#     });
# </script>
#     """
#
# # @app.route('/logout')
# # def logout():
# #     session.clear()
#
# @socketio.on('connect')
# def handle_message():
#     print('someone connected')
#
# @socketio.on('message')
# def handle_message(message):
#     room = session['room']
#     send(message, room=room)
#
# @socketio.on('join')
# def on_join(data):
#     # username = session['user'].get('username')
#     # room = username + data['other']
#     username = data['username']
#     room = data['room']
#     join_room(room)
#     session['room'] = room
#     send('Oi dickhead, join this room ' + room)
#     send(username + ' has entered the room.', room=room)
#     send('blah', room='qwer')
#     emit('message', 'blah', room='qwer')
#
# @socketio.on('leave')
# def on_leave(data):
#     # username = session['user'].get('username')
#     # room = username + data['other']
#     username = data['username']
#     room = data['room']
#     leave_room(room)
#     send(username + ' has left the room.', room=room)
#
# if __name__ == '__main__':
#     socketio.run(app)

from flask import Flask, render_template, session, jsonify
from flask_socketio import SocketIO, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from server.models import Conversation, Messages, User_Profile, Match, Right_Swipe, db
from Classes.recommendation_system import Recommendation_System, Right_Swipes
from Classes.message_system import Message_System
from datetime import datetime, date

# from flask import Flask
# from flask_bootstrap import Bootstrap
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager
# from flask_jsglue import JSGlue
# from config import Config
#
# # Extension Initialisation
# bootstrap = Bootstrap()
# db = SQLAlchemy()
# login_manager = LoginManager()
# login_manager.login_view = 'auth.login'
# jsglue = JSGlue()
#
# # Factory Function
# def create_app():
#     # Create Flask Instance
#     app = Flask(__name__, static_url_path='/static')
#     app.config.from_object(Config)
#
#     # Apply Extension to Flask Instance
#     bootstrap.init_app(app)
#     db.init_app(app)
#     login_manager.init_app(app)
#     jsglue.init_app(app)

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = 'user_side#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test1.db'
db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
    db.create_all()

# This is the first function, once called, it should return the match recommendations
@app.route('/')
def get_recommendations():
# def sessions(origin):

    origin = "Main Library, University of New South Wales, Sydney, Australia"
    recs_sys = Recommendation_System()
    # current_user_id = current_user.id
    current_user_id = 1
    user = User_Profile.query.filter_by(id=current_user_id).first()
    user.location = origin
    db.session.commit()
    recommendations = recs_sys.getRecommendations(origin)
    print(len(recommendations))
    # To print during pytest, uncomment False Assertion
    for recommendation in recommendations:
        # event.user_id = owner.id
        print("########################")
        print("Username: ", recommendation['match_user_username'])
        print("Distance: ", recommendation['distance'])
    return jsonify(recommendations)
    # return render_template('index.html', recommendations=recommendations)

@app.route("/get_conversations")
def get_conversations():

    message_sys = Message_System()
    conversations = message_sys.getConversations()
    for conversation in conversations:
        print("########################")
        # print("First Name: ", recommendation.f_name)
        # print ("Last Name: ", recommendation.l_name)
        # print("addr: ", event.addr)
        # print("start: ", event.start_time)
        # print("end: ", event.end_time)
        print("Username: ", conversation['username'])
        print("Last_Message: ", conversation['last_message'])
        print("Time: ", conversation['time'])
    return jsonify(conversations)
    # return render_template('conversations.html', conversations=conversations)

@app.route("/get_conversation_messages/<room_id>")
def get_conversation_messages(room_id):
    message_sys = Message_System()
    conversation, messages = message_sys.getMessages(room_id)
    print("########################")
    print("Username: ", conversation['conversation_username'])
    print("***********************")
    for message in messages:
        print("Message Sender: ", message['message_username'])
        print("Message: ", message['message'])
        print("Time: ", message['time_sent'])
    return jsonify({'conversation': conversation, 'messages': messages})
    # return render_template('messages.html', conversation=conversation, messages=messages)

def messageReceived():
    print('message was received!!!')

# This message should be called when the user is trying to send a message, to an existing
# conversation
@socketio.on('send_message')
def handle_send_message(json):
    print('received my event: ' + str(json))
    current_user_id = 3
    username = User_Profile.query.filter_by(username=json['user_name']).first()
    if username is None:
        socketio.emit('my response', json, callback="Something is wrong, Username cannot be found")
        exit(100)

    conversation = Conversation.query.filter_by(username_one=username.id).filter_by(username_two=current_user_id).first()
    if conversation is None:
        conversation = Conversation.query.filter_by(username_two=username.id).filter_by(username_one=current_user_id).first()
    if conversation is None:
        socketio.emit('my response', json, callback="Something is wrong, Conversation Room cannot be found")
        exit(200)
    room = conversation.room
    message = Messages(room=room,
                       sender_username=username.id,
                       time_sent=datetime.now(),
                       message=json['message'])
    db.session.add(message)
    db.session.commit()
    socketio.emit('my response', json, callback=messageReceived)

#This function should be called when the user right-swipes on an individual
@socketio.on('join')
def on_join(match_dict):
    right_swipes = Right_Swipes()
    current_user_id = 3
    target_id = User_Profile.query.filter_by(username=match_dict['match_user_username']).first().id
    previous_swipe = right_swipes.right_swipes(match_dict, current_user_id, target_id)
    if previous_swipe == 1:
        second_right_swipe = Right_Swipe(time=datetime.now(),
                                         swiper_id=current_user_id,
                                         target_id=target_id,
                                         became_match=True)
        db.session.add(second_right_swipe)
        db.session.commit()
        room_id = str(target_id) + "+" + str(current_user_id)
        conversation = Conversation(room=room_id,
                                    username_one=target_id,
                                       username_two=current_user_id)
        db.session.add(conversation)
        db.session.commit()
        match = Match(distance=match_dict['distance'],
                      created=datetime.now(),
                      first_swiper=target_id,
                      second_swiper=current_user_id,
                      conversation_id=room_id)
        db.session.add(match)
        db.session.commit()
        found_match = {"succesful_error_message": "Found a match",
                       "successful_error_code": 0}
        code = found_match
        # socketio.emit("join_response", found_match)
    elif previous_swipe == -1:
        first_right_swipe = Right_Swipe(time=datetime.now(),
                                        swiper_id=current_user_id,
                                        target_id=target_id)
        db.session.add(first_right_swipe)
        db.session.commit()
        first_right_swipe = {"successful_error_message": "Request has been included into our system",
                             "successful_error_code": 1}
        code = first_right_swipe
        # socketio.emit("join_response", first_right_swipe)
    else:
        error_code = {"successful_error_message": "Something went wrong",
                      "successful_error_code": -1}
        code = error_code
    return code
    # socketio.emit("join_response", error_code)

if __name__ == '__main__':
    socketio.run(app, debug=True)