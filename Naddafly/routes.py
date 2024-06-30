from datetime import datetime

from Naddafly import app, db
from flask import render_template, request, redirect, url_for, flash ,send_from_directory ,send_file
from Naddafly.models import Garbage, Detector, Collector, User, Rewards, Region
from Naddafly.Ai_Model.ai import process_image
from flask import Flask, jsonify, request, render_template, redirect
from flask_login import login_user, logout_user, login_required, current_user



@app.route('/home')
@app.route('/')
def index():
    return 'Eiad Says Hello!, Welcome to Naddafly! \n try /swagger/'



@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')

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
    detector = Detector.query.filter_by(id=current_user.id).first()
    redeemed = None
    print(detector.score)
    print(detector.username)
    if detector.score >= 10:
        redeemed = Rewards.query.filter_by(userId=None).first()

    if redeemed:
        detector.score -= 10
        redeemed.userId = current_user.id
        db.session.commit()
        return jsonify({'reward': redeemed.to_dict()}), 200
    else:
        return jsonify({'error': 'Reward not found'}), 404


@app.route('/user_rewards', methods=['GET'])
@login_required
def user_rewards():
    rewards = Rewards.query.filter_by(userId=current_user.id).all()
    rewards_list = []
    for reward in rewards:
        rewards_list.append(reward.to_dict())
    return jsonify({'rewards': rewards_list}), 200


@app.route('/login', methods=['POST'])
def login_page():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if username:
        attempted_user = User.query.filter_by(username=username).first()
    else:
        attempted_user = User.query.filter_by(email_address=email).first()

    if attempted_user and attempted_user.check_password_correction(
            attempted_password=password
    ):
        idd = attempted_user.id
        if attempted_user.discriminator == 'detector':
            attempted_user = Detector.query.filter_by(id=idd).first()
        else:
            attempted_user = Collector.query.filter_by(id=idd).first()

        login_user(attempted_user)
        flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
        print(attempted_user.to_dict())
        return jsonify({'user': attempted_user.to_dict()}), 200

    else:
         return jsonify({'user': 'bad'}), 404


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("index"))


@app.route("/upload-image", methods=["POST"])
@login_required
def upload_image():
    latitude = float(request.form.get('latitude'))
    longitude = float(request.form.get('longitude'))
    image = request.files['image']
    if not latitude or not longitude :
        return jsonify({'error': 'Latitude, longitude and image are required'}), 400
    if not image:
        return jsonify({'error': 'Image is required'}), 400
    print(latitude)
    print(longitude)

    if latitude is None or longitude is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    image = request.files['image']
    process_image(image, current_user, request, latitude, longitude)
    detector = Detector.query.filter_by(id=current_user.id).first()
    return jsonify({'score': detector.score}), 200


@app.route("/map", methods=["GET"])

@login_required
def map_page():
    print("ay 7aga")
    data = User.query.filter_by(id=current_user.id).first().discriminator
    print(data)
    if data != 'collector':
        return jsonify({'error': 'Only garbage collectors can access this feature'}), 403

    garbages = Garbage.query.filter_by(is_collected=False).all()
    garbages_dict = [garbage.to_dict() for garbage in garbages]
    print(garbages_dict)
    return jsonify(garbages_dict) ,200
 
@app.route("/map-img", methods=["GET"])


@app.route("/remove-garbage/<int:garbage_id>", methods=["POST"])

@login_required
def remove_garbage_page(garbage_id):
    data = User.query.filter_by(id=current_user.id).first().discriminator
    print(data)
    if data != 'collector':
        return jsonify({'error': 'Only garbage collectors can remove garbage markers'}), 403

    garbage = Garbage.query.get(garbage_id)
    if garbage and not garbage.is_collected:
        garbage.is_collected = True
        garbage.collection_date = datetime.now()

        collector = Collector.query.filter_by(id=current_user.id).first()
        if collector:
            collector.garbageCollected += 1

        db.session.commit()
        return jsonify({"message": "Garbage marker removed successfully","garbageCollected": collector.garbageCollected}), 200
    else:
        return jsonify({"error": "Garbage not found"}), 404
