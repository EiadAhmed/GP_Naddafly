from datetime import datetime

from Naddafly import app, db
from flask import render_template, request, redirect, url_for, flash
from Naddafly.models import Garbage, Detector, Collector, User, Rewards, Region
from Naddafly.Ai_Model.ai import process_image
from flask import Flask, jsonify, request, render_template, redirect
from flask_login import login_user, logout_user, login_required, current_user



@app.route('/home')
@app.route('/')
def index():
    return 'Eiad'


# @app.route("/create-region", methods=["POST"])
# def create_region():
#     # Parse JSON data from the request body
#     data = request.json

#     # Extract name and polygon from the JSON data
#     name = data.get("name")
#     polygonx = data.get("polygon")
#     polygon = WKTElement(polygonx, srid=4326)  # Assuming SRID 4326 (WGS 84)
#     print(polygon)

#     # Check if name and polygon are provided
#     if not name or not polygon:
#         return jsonify({"error": "Both name and polygon are required"}), 400

#     # Create a new Region instance
#     new_region = Region(name=name, polygon=polygon)
#     print("ay 7aga")

#     try:
#         # Add the new region to the database
#         db.session.add(new_region)
#         db.session.commit()

#         # Display region info
#         region_info = {
#             "id": new_region.id,
#             "name": new_region.name,
#             "polygon": new_region.polygon
#         }
#         print("ay 7aga2222222222222222")

#         return jsonify({
#             "message": "Region created successfully",
#             "region": region_info
#         }), 201
#     except Exception as e:
#         # Rollback the transaction if an error occurs
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500


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
        flash('Username and password are not match! Please try again', category='danger')


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("index"))


@app.route("/upload-image", methods=["POST"])
@login_required
def upload_image():
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    if latitude is None or longitude is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    image = request.files['image']
    process_image(image, current_user, request, latitude, longitude)

    return jsonify({'success': True}), 200


@app.route("/map", methods=["GET"])
@login_required
def map_page():
    data = User.query.filter_by(id=current_user.id).first().discriminator
    print(data)
    if data != 'collector':
        return jsonify({'error': 'Only garbage collectors can access this feature'}), 403

    garbages = Garbage.query.filter_by(is_collected=False).all()
    garbages_dict = [garbage.to_dict() for garbage in garbages]
    print(garbages_dict)
    return jsonify(garbages_dict)
    garbage_locations = [{"latitude": garbage.latitude, "longitude": garbage.longitude} for garbage in garbages]
    print(garbages)
    return jsonify({ garbages}), 200


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
        db.session.commit()
        return jsonify({"message": "Garbage marker removed successfully"}), 200
    else:
        return jsonify({"error": "Garbage not found"}), 404