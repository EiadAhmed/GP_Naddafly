from datetime import *
from secrets import token_urlsafe
from flask import Flask, send_from_directory, abort
import os
from flask_login import UserMixin
# from geoalchemy2 import Geometry
from Naddafly import db, app
from Naddafly import login_manager

from Naddafly import bcrypt
from sqlalchemy import func
from flask import url_for
import base64


# from sqlalchemy.ext.compiler import compiles
# from sqlalchemy.sql.expression import FunctionElement


# class ST_GeomFromText(FunctionElement):
#     name = "ST_GeomFromText"


# @compiles(ST_GeomFromText)
# def compile(element, compiler, **kw):
#     return "ST_GeomFromText(%s, %s)" % (compiler.process(element.clauses), element.kwargs.get('srid', 0))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    discriminator = db.Column(db.String(50))

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    def disc_fun(self):
        return {}

    def to_dict(self):
        return {
            'id': str(self.id),
            'username': self.username,
            'email_address': self.email_address,
            'is_verified': self.is_verified,
            'discriminator': self.discriminator,

        } | self.disc_fun()


class Detector(User):
    score = db.Column(db.Integer(), default=0)

    def disc_fun(self):
        return {
            'score': self.score
        }


class Collector(User):
    collectorId = db.Column(db.String(length=30), unique=True)
    regionId = db.Column(db.String(length=30), unique=True)
    garbageCollected = db.Column(db.Integer(), default=0)

    def disc_fun(self):
        return {
            'collectorId': self.collectorId,
            'regionId': self.regionId,
            'garbageCollected': self.garbageCollected
        }

def save_image_to_server(binary_data):
    # Define the directory where you want to save the image
    save_directory = "static/images/"
  
    
    try:
       
        url =  url_for('static', filename=f"images/{binary_data}")
       
        return url
    
    except Exception as e:
        print(f"Error saving image to server: {e}")
        return "Error"
class Garbage(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    latitude = db.Column(db.String(length=30), nullable=False)
    longitude = db.Column(db.String(length=30), nullable=False)
    owner = db.Column(db.Integer(), db.ForeignKey('user.id'))
    is_collected = db.Column(db.Boolean, nullable=False, default=False)
    collection_date = db.Column(db.DateTime)
    detection_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    volume = db.Column(db.String(), default=0)
    img = db.Column(db.String(length=255), nullable=False, default='')

    def to_dict(self):
        img_data = None
        
        try:
           
            img_data = save_image_to_server(self.img)
        except Exception as e:
            print(f"Error loading image: {e}")
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'owner': self.owner,
            'is_collected': self.is_collected,
            'collection_date': self.collection_date,
            'detection_date': self.detection_date,
            'volume': self.volume,
            'img': img_data
        }

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # polygon = db.Column((Geometry(geometry_type='POLYGON', srid=4326)), nullable=False, default='')

class Rewards(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userId = db.Column(db.Integer(), db.ForeignKey('user.id'))
    platform = db.Column(db.String(length=30), nullable=False)
    discount = db.Column(db.Float(), nullable=False)
    description = db.Column(db.String(length=1000), nullable=False)
    expiration_date = db.Column(db.DateTime, default=datetime.now)
    voucher_code = db.Column(db.String(length=60), nullable=False, unique=True)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.userId,
            'platform': self.platform,
            'discount': self.discount,
            'description': self.description,
            'expiration_date': self.expiration_date.isoformat(),
            'voucher_code': self.voucher_code
        }


with app.app_context():
    def generate_vouchers(num_vouchers, platform, discount, description, days):
        for _ in range(num_vouchers):
            # Generate a random voucher_code
            # while True:
            #     # Generate a random token as the voucher_code
            new_voucher_code = token_urlsafe(20)  # Adjust the length as needed
            #
            #     # Check if the generated voucher_code already exists in the database
            #     existing_voucher = Rewards.query.filter_by(voucher_code=new_voucher_code).first()
            #     if not existing_voucher:
            #         break  # Exit the loop if the voucher_code is unique

            # Create a new Rewards object with the provided parameters
            new_reward = Rewards(
                platform=platform,
                discount=discount,
                description=description,
                expiration_date=datetime.now() + timedelta(days=days),
                voucher_code=new_voucher_code
            )

            # Add the new_reward to the session and commit to the database
            db.session.add(new_reward)
            db.session.commit()
