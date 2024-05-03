from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
from functools import wraps
import os
import cv2
import dlib
import base64
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
from collections import defaultdict

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['MONGO_URI'] = 'YOUR URI CONNECTION STRING HERE'
app.secret_key = 'thisisasecretkey'
mongo = PyMongo(app)

# MongoDB configuration
client = MongoClient('YOUR URI CONNECTION STRING HERE')
db = client['attendance']

# Collection for attendance records
attendance_records = db['attendance_records']

# Collection for learning data
learn_collection = db['learn_data']

access_granted = False  # Initialize access status

# Maintain a set of recognized persons and their attendance status
recognized_persons = set()

# Load the pre-trained face recognition model from dlib
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_recognizer = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

# Global variable to store known faces
known_faces = {}

""" @app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
 """
def authorize_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'message': 'Unauthorized access!'}), 401
        if session.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized access!'}), 403
        return func(*args, **kwargs)
    return wrapper

def authorize_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'message': 'Unauthorized access!'}), 401
        if session.get('role') != 'user':
            return jsonify({'message': 'Unauthorized access!'}), 403
        return func(*args, **kwargs)
    return wrapper

def authorize_staff(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'message': 'Unauthorized access!'}), 401
        if session.get('role') != 'staff':
            return jsonify({'message': 'Unauthorized access!'}), 403
        return func(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    return render_template('index.html')


# Handle login for both GET and POST requests 
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = mongo.db.creds.find_one({'username': username, 'password': password})

    if user:
        session['username'] = username
        session['role'] = user['role']

        return jsonify({'message': 'Successfully logged in!', 'role': user['role']})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))

# Example routes with authentication
@app.route('/admin', methods=['GET', 'POST'])
@authorize_admin
def admin():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        title = request.form.get('title')
        username = request.form.get('username')
        password = request.form.get('password')
        uid = request.form.get('uid')
        

        # Insert data into 'staff' collection
        mongo.db.staff.insert_one({
            'name': name,
            'email': email,
            'title': title,
            'role':'staff',
            'uid': uid
        })

        # Insert data into 'creds' collection
        mongo.db.creds.insert_one({
            'username': username,
            'password': password,
            'role':'staff',
            'uid': uid
        })

        # Redirect to the admin route to fetch and display updated data
        return redirect(url_for('admin'))

    else:
        # Fetch initial data from collections
        staff_data = mongo.db.staff.find()
        user_data = mongo.db.user.find()
        return render_template('admin.html', staff_data=staff_data, user_data=user_data)
    
# Modify the route to handle staff deletion
@app.route('/delete_staff', methods=['POST'])
def delete_staff():
    staff_id = request.form['staff_id']  # Retrieve staff ID from form data

    # Retrieve the UID of the staff member from the form data
    staff_uid = request.form['staff_uid']

    # Delete staff data from the 'staff' collection
    mongo.db.staff.delete_one({'_id': ObjectId(staff_id)})  # Assuming you are using ObjectId for staff_id

    # Delete staff data from the 'creds' collection based on UID
    mongo.db.creds.delete_one({'uid': staff_uid})

    return redirect(url_for('admin'))  # Redirect back to admin page after deletion

def calculate_monthly_attendance(username):
    monthly_attendance = defaultdict(int)

    # Fetch attendance data for the user
    attendance_data = fetch_attendance_data_for_user(username)

    # Count the number of present days for each month
    for record in attendance_data:
        month = record['date'].split('-')[1]
        if record['status'] == 'Present':
            monthly_attendance[month] += 1

    # Calculate the percentage attendance for each month
    attendance_percentages = {}
    for month, present_days in monthly_attendance.items():
        total_days = len([record for record in attendance_data if record['date'].split('-')[1] == month])
        attendance_percentage = (present_days / total_days) * 100 if total_days > 0 else 0
        attendance_percentages[month] = round(attendance_percentage, 2)

    return attendance_percentages

@app.route('/user')
@authorize_user
def user():
    username = session.get('username')
    user_data = mongo.db.creds.find_one({'username': username})
    
    if user_data:
        uid = user_data.get('id')
        user_profile = mongo.db.user.find_one({'uid': uid})
        
        if user_profile:
            user_name = user_profile.get('name')
            img_folder = user_profile.get('img_folder')
            profile_image_path = url_for('static', filename=f'images/profile/{img_folder}/profile.jpg')
            
            # Fetch attendance data for the user for the current year and month
            selected_month = request.args.get('month', datetime.now().month, type=int)
            print(selected_month)
            year = datetime.now().year
            attendance_data = fetch_attendance_data_for_user(user_name, year, selected_month)

            present_count = sum(1 for record in attendance_data if record['status'] == 'Present')
            absent_count = sum(1 for record in attendance_data if record['status'] == 'Absent')

            notifications = mongo.db.messages.find({'recipient': 'user', 'sender': 'staff'}).sort([('timestamp', -1)])

            birthdate_data = mongo.db.user.find({}, {'name': 1, 'birthdate': 1})

            birthdate_data_formatted = []
            for user in birthdate_data:
                birthdate_str = user['birthdate']  # Assuming 'birthdate' is a string
                birthdate_obj = datetime.strptime(birthdate_str, '%Y-%m-%d')  # Convert string to datetime object
                user['birthdate'] = datetime.strftime(birthdate_obj, '%d-%m-%Y')
                birthdate_data_formatted.append(user)

            
            
            return render_template('user.html', 
                                   profile_image_path=profile_image_path,
                                   user_name=user_name,
                                   attendance_data=attendance_data,
                                   birthdate_data=birthdate_data_formatted,
                                   present_count=present_count,
                                   absent_count=absent_count,
                                   notifications=notifications)  # Pass attendance data to the template
        else:
            return jsonify({'message': 'User profile not found!'}), 404
    else:
        return jsonify({'message': 'User data not found!'}), 404


def calculate_attendance_percentage(attendance_data_monthly):
    total_days = len(attendance_data_monthly)
    total_present_days = sum(1 for record in attendance_data_monthly if record['status'] == 'Present')
    
    # Calculate percentage attendance
    if total_days > 0:
        attendance_percentage = (total_present_days / total_days) * 100
    else:
        attendance_percentage = 0
    
    return attendance_percentage

@app.route('/attendance_percentage')
def attendance_percentage():
    username = session.get('username')
    user_data = mongo.db.creds.find_one({'username': username})
    
    if user_data:
        uid = user_data.get('id')
        user_profile = mongo.db.user.find_one({'uid': uid})
        
        if user_profile:
            user_name = user_profile.get('name')
            # Fetch attendance data for the user
            attendance_data = fetch_attendance_data_for_user(user_name, 2024, 3)
            
            # Calculate attendance percentage
            attendance_percentage = calculate_attendance_percentage(attendance_data)
            
            return jsonify({'attendance_percentage': attendance_percentage})
        else:
            return jsonify({'message': 'User profile not found!'}), 404
    else:
        return jsonify({'message': 'User data not found!'}), 404

def fetch_attendance_data_for_user(username, year, month):
    # Construct the start and end dates for the month
    start_date = datetime(year, month, 1)
    end_date = datetime.now()  # Set end date to the first day of the next month

    # Initialize a list to store attendance data for the entire month
    attendance_data_monthly = []

    # Iterate over each day of the month
    current_date = start_date
    while current_date < end_date:
        # Get the date in the format YYYY-MM-DD
        formatted_date = current_date.strftime("%d-%m-%Y")

        # Retrieve attendance data for the current date from attendance_records collection
        attendance_data_daily = list(attendance_records.find({'name': username, 'date': formatted_date}))

        if attendance_data_daily:
            # Attendance data found for the current date
            for record in attendance_data_daily:
                attendance_data_monthly.append({
                    'name': record['name'],
                    'date': formatted_date,
                    'time': record.get('time', '-'),
                    'status': record['status']
                })
        else:
            # No attendance data found for the current date, mark as 'Absent' and append to the monthly list
            attendance_data_monthly.append({
                'name': username,
                'date': formatted_date,
                'time': '-',
                'status': 'Absent'
            })

        # Move to the next day
        current_date += timedelta(days=1)


    return attendance_data_monthly


@app.route('/staff', methods=['GET', 'POST'])
@authorize_staff
def staff():
    if request.method == 'POST':
        if 'name' in request.form:  # Form submission for adding a new user
            name = request.form.get('name')
            email = request.form.get('email')
            birthdate = request.form.get('birthdate')
            username = request.form.get('username')
            password = request.form.get('password')
            uid = request.form.get('uid')
            

            # Insert data into 'user' collection
            mongo.db.user.insert_one({
                'name': name,
                'email': email,
                'role': 'user',
                'birthdate': birthdate,
                'uid': uid,
                'img_folder': username
            })

            # Insert data into 'creds' collection
            mongo.db.creds.insert_one({
                'username': username,
                'password': password,
                'role': 'user',
                'id': uid
            })

            # Redirect to the staff route to fetch and display updated data
            return redirect(url_for('staff'))

        elif 'notification' in request.form:  # Form submission for uploading a notification
            notification_message = request.form.get('notification')
            mongo.db.messages.insert_one({
                'recipient': 'user',
                'sender': 'staff',
                'message': notification_message,
                'timestamp': datetime.now()
            })

            # Redirect to the staff route to fetch and display updated data
            return redirect(url_for('staff'))

    else:  # GET request handling
        # Fetch attendance data
        attendance_data = fetch_attendance_data(2024, 3)
        unique_names = set(record['name'] for record in attendance_data)
        unique_dates = set(record['date'] for record in attendance_data)
        unique_dates = sorted(unique_dates)

        # Fetch user data
        user_data = mongo.db.user.find()
        return render_template('staff.html', user_data=user_data, attendance_data=attendance_data, unique_names=list(unique_names), unique_dates=unique_dates)
 

def fetch_attendance_data(year, month):
    # Construct the start and end dates for the month
    start_date = datetime(year, month, 1)
    end_date = datetime.now()  # Set end date to the first day of the next month

    # Initialize a list to store attendance data for the entire month
    attendance_data_monthly = []

    # Iterate over each day of the month
    current_date = start_date
    while current_date < end_date:
        # Get the date in the format YYYY-MM-DD
        formatted_date = current_date.strftime("%d-%m-%Y")

        # Retrieve attendance data for the current date from attendance_records collection
        attendance_data_daily = list(attendance_records.find({'date': formatted_date}))

        if attendance_data_daily:
            # Attendance data found for the current date
            for record in attendance_data_daily:
                attendance_data_monthly.append({
                    'name': record['name'],
                    'date': formatted_date,
                    'time': record.get('time', '-'),
                    'status': record['status']
                })
        else:
            # No attendance data found for the current date, mark as 'Absent' for all users
            user_data = mongo.db.user.find({}, {'name': 1})
            for user in user_data:
                attendance_data_monthly.append({
                    'name': user['name'],
                    'date': formatted_date,
                    'time': '-',
                    'status': 'Absent'
                })

        # Move to the next day
        current_date += timedelta(days=1)

    return attendance_data_monthly


@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    if request.method == 'POST':
        # Retrieve form data
        record_name = request.form['record_name']
        record_date = request.form['record_date']

        # Check if the attendance toggle field is present in the form data
        if 'attendance-toggle' in request.form:
            toggle_value = request.form.get('attendance-toggle')
            new_status = 'Present' if toggle_value == 'on' else 'Absent'
            time = datetime.now().strftime("%H:%M:%S")  # Get the current time
        else:
            new_status = 'Absent'  # Set default status if toggle field is not present
            time = '-'

        # Update the attendance status in the attendance_records collection
        attendance_records.update_one({'name': record_name, 'date': record_date}, {'$set': {'status': new_status,'time':time}})

        return redirect(url_for('staff'))  # Redirect back to staff page after updating attendance status


# Modify the route to handle staff deletion
@app.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']  # Retrieve user ID from form data

    # Retrieve the UID of the user from the form data
    user_uid = request.form['user_uid']

    # Delete staff data from the 'staff' collection
    mongo.db.user.delete_one({'_id': ObjectId(user_id)})  # Assuming you are using ObjectId for user_id

    # Delete staff data from the 'creds' collection based on UID
    mongo.db.creds.delete_one({'id': user_uid})

    return redirect(url_for('staff'))  # Redirect back to staff page after deletion

@app.route('/toggle_access', methods=['POST'])
def toggle_access():
    global access_granted
    data = request.get_json()
    access_granted = data.get('accessGranted')
    return jsonify({'status': 'success', 'message': 'Access toggled successfully'})

@app.route('/check_access')
def check_access():
    return jsonify({'accessGranted': access_granted})

@app.route('/video')
@authorize_user
def face():
    username = session.get('username')
    user_data = mongo.db.creds.find_one({'username': username})
    
    if user_data:
        uid = user_data.get('id')
        user_profile = mongo.db.user.find_one({'uid': uid})
        
        if user_profile:
            user_name = user_profile.get('name')
            img_folder = user_profile.get('img_folder')
            profile_image_path = url_for('static', filename=f'images/profile/{img_folder}/profile.jpg')
            
            # Check if today's attendance record already exists
            today_date = datetime.now().strftime("%d-%m-%Y")
            existing_record = db.attendance_records.find_one({'name': user_name, 'date': today_date, 'status': "Present"})
            
            if existing_record:
                error_message = f'Attendance already recorded for {user_name} today'
                return jsonify({'error': error_message})
            
            return render_template('face.html', profile_image_path=profile_image_path, user_name=user_name)
        
        else:
            return jsonify({'message': 'User profile not found!'}), 404
    else:
        return jsonify({'message': 'User data not found!'}), 404


# Define the route for real-time face recognition
@app.route('/capture', methods=['POST'])
def capture():
    try:
        # Decode base64 image
        image_data_url = request.json['image']
        _, encoded = image_data_url.split(",", 1)
        decoded = base64.b64decode(encoded)
        np_arr = np.frombuffer(decoded, dtype=np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # Perform face recognition
        recognized_name = recognize_face(img)
        print(recognized_name)

        if recognized_name:
            # Check if today's attendance record already exists for the recognized person
            today_date = datetime.now().strftime("%d-%m-%Y")

            # Insert new attendance record
            db.attendance_records.update_one({
                'name': recognized_name,
                'date': today_date
                },{'$set': {
                'username': session.get('username'),
                'status': 'Present',
                'time': datetime.now().strftime("%H:%M:%S")
            }})

            return jsonify({'status': 'success', 'message': f'Attendance recorded for {recognized_name}', 'redirect_url': '/user'})
        else:
            return jsonify({'status': 'fail', 'message': 'Face not recognized'})

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error processing the image'})


def learn_faces_from_images(images_folder):
    global known_faces
    known_faces = {}
    
    for person_name in os.listdir(images_folder):
        person_path = os.path.join(images_folder, person_name)
        if os.path.isdir(person_path):
            person_images = [cv2.imread(os.path.join(person_path, img)) for img in os.listdir(person_path)]
            person_face_descriptors = []

            for img in person_images:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector(gray)

                if faces:
                    landmarks = predictor(gray, faces[0])
                    face_descriptor = face_recognizer.compute_face_descriptor(img, landmarks)
                    person_face_descriptors.append(face_descriptor)

            if person_face_descriptors:
                # Store the mean face descriptor for each person
                known_faces[person_name] = np.mean(person_face_descriptors, axis=0)

    return known_faces

def recognize_face(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)
        face_descriptor = face_recognizer.compute_face_descriptor(img, landmarks)

        # Compare with known faces in the learning collection
        for name, known_descriptor in known_faces.items():
            distance = np.linalg.norm(face_descriptor - known_descriptor)

            # Set a threshold for face recognition
            if distance < 0.6:
                return name  # Face recognized

    return None  # Face not recognized

def add_initial_attendance_records():
    # Get today's date in the required format
    today_date_str = datetime.now().strftime('%d-%m-%Y')

    # Retrieve user data from the 'user' collection
    user_data = mongo.db.user.find({}, {'name': 1, 'uid': 1})

    # Retrieve creds data from the 'creds' collection
    creds_data = mongo.db.creds.find({}, {'username': 1, 'id': 1})

    # Initialize a dictionary to map uid to username
    uid_to_username = {cred['id']: cred['username'] for cred in creds_data}

    # Get the attendance_records collection
    attendance_records = db.attendance_records

    # Iterate over user data to link names with usernames based on uid and id
    for user in user_data:
        if user['uid'] in uid_to_username:
            # Fetch the corresponding username based on uid
            username = uid_to_username[user['uid']]
            name = user['name']

            # Check if there's an existing record for the same name and date
            existing_record = attendance_records.find_one({'name': name, 'date': today_date_str})

            if existing_record:
                # If record exists for the same name and date, skip
                continue

            # Insert attendance record into attendance_records collection with status 'Absent'
            result = attendance_records.insert_one({
                'name': name,
                'username': username,
                'status': 'Absent',
                'date': today_date_str
            })


if __name__ == '__main__':
    print("Adding initial attendance records...")
    add_initial_attendance_records()
    print("Initial attendance records added successfully!")
    # Learn faces from images when the server starts
    print("learning faces from images...")
    images_folder = "images"  # Update with your images folder path
    learn_faces_from_images(images_folder)
    print("Faces learned successfully!")
    app.run(debug=True)
