from Naddafly import app, db
from flask import render_template, request, redirect, url_for, flash
from Naddafly.models import Garbage, Detector, Collector, User, Rewards
from Naddafly.Ai_Model.ai import process_image
from flask import Flask, jsonify, request, render_template, redirect
from flask_login import login_user, logout_user, login_required, current_user


@app.route('/home')
@app.route('/')
def index():
    return 'Eiad'


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')  # Add user_type field to specify the type of user

    if not username or not email or not password or not user_type:
        return jsonify({'message': 'All fields are required'}), 400

    if user_type == 'detector':
        existing_user = Detector.query.filter_by(username=username).first()
        existing_user2 = Detector.query.filter_by(email_address=email).first()
    elif user_type == 'collector':
        existing_user = Collector.query.filter_by(username=username).first()
        existing_user2 = Collector.query.filter_by(email_address=email).first()
    else:
        return jsonify({'message': 'Invalid user type'}), 400

    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400
    if existing_user2:
        return jsonify({'message': 'Email already exists'}), 400

    user = None
    if user_type == 'detector':
        user = Detector(username=username, email_address=email, discriminator=user_type)
    elif user_type == 'collector':
        user = Collector(username=username, email_address=email, collectorId=data.get('collectorId')
                         , discriminator=user_type)

    user.password = password
    print(user)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash(f"Account created successfully! You are now logged in as {user.username}", category='success')
    return jsonify({'message': 'User created'}), 200


@app.route('/redeem', methods=['GET'])
@login_required
def redeem():
    redeemed = None
    if current_user.score > 10:
        redeemed = Rewards.query.filter_by(userId=None).first()

    if redeemed:

        current_user.score -= 10
        redeemed.userId = current_user.id
        db.session.commit()
        return jsonify({'reward': redeemed}), 200
    else:
        return jsonify({'message': 'try again  on another time '}), 400


@app.route('/user_rewards', methods=['GET'])
@login_required
def user_rewards():
    rewards = Rewards.query.filter_by(userId=current_user.id)

    return jsonify({'rewards': rewards}), 200


@app.route('/login', methods=['POST'])
def login_page():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if username:
        attempted_user = User.query.filter_by(username=username.data).first()
    else:
        attempted_user = User.query.filter_by(email_address=email.data).first()

    if attempted_user and attempted_user.check_password_correction(
            attempted_password=password
    ):
        login_user(attempted_user)
        flash(f'Success! You are logged in as: {attempted_user.username}', category='success')

    else:
        flash('Username and password are not match! Please try again', category='danger')

    return jsonify({'message': f'Done '}), 200


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))


@app.route("/upload-image", methods=["POST"])
@login_required
def upload_image():
    image = request.files['image']
    process_image(image, current_user, request)

    return "DONE", 200
