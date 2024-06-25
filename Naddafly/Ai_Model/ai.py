from datetime import datetime

from ultralytics import YOLO
from keras.models import load_model
from PIL import Image
import tensorflow as tf
import numpy as np
import glob
import os
import shutil
import json
from Naddafly import db
from Naddafly.models import Garbage, Detector, Collector, User
from math import radians, cos, sin, sqrt, atan2


# yolo

yoloModel = YOLO('Naddafly/Ai_Model/best.pt')


def detect(raw_image, yoloModel):
    yoloModel(raw_image, save_txt=False, project="Naddafly/Ai_Model/Model", name="Labels", save_crop=True)


# volume estimation

# variables
model = load_model('Naddafly/Ai_Model/volume.h5')
images_folder = 'Naddafly/Ai_Model/Model/Labels/crops/garbage/'

# move
destination_folder = 'Naddafly/Ai_Model/finished/'
labels_folder = 'Naddafly/Ai_Model/Model/Labels/'


# prediction

def Predict(model, images_folder):
    image_paths = glob.glob(images_folder + '*.jpg') + glob.glob(images_folder + '*.jpeg') + glob.glob(
        images_folder + '*.png')
    results = []
    for image_path in image_paths:
        img = Image.open(image_path)
        resize = tf.image.resize(img, (256, 256))
        yhat = model.predict(np.expand_dims(resize / 255, 0), verbose=False)
        size = 'large' if yhat < 0.5 else 'small'
        confidence_percentage = yhat * 100 if size == 'small' else (1 - yhat) * 100

        image_file = os.path.basename(image_path)
        # print("Path", image_path, ":","confidence precentage", confidence_percentage,'size' , ':',size)

        result = {
            "image": image_file,
            "Confidence": float(confidence_percentage),
            "size": size
        }
        results.append(result)
    return results


# delete and move

def MoveAndDel(images_folder, destination_folder, labels_folder, json_data):
    if json_data:
        if os.path.exists(destination_folder):
            idx = 1
            while os.path.exists(destination_folder + f'_{idx}'):
                idx += 1
            destination_folder = destination_folder + f'_{idx}'
        os.makedirs(destination_folder)
        with open(os.path.join(destination_folder, "data.json"), 'w') as f:
            json.dump(json_data, f, indent=4)
        shutil.move(images_folder, destination_folder)
        shutil.rmtree(labels_folder)


raw_images_dir = 'Naddafly/static/images'


def calc_distance(lat1, lon1, lat2, lon2):
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) * sin(dlat / 2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) * sin(dlon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c * 1000
    return distance

def is_near_existing_garbage(latitude, longitude):
    garbages = Garbage.query.all()
    for garbage in garbages:
        distance = calc_distance(float(latitude), float(longitude), float(garbage.latitude),float( garbage.longitude))
        if distance < 15:
            return True
    return False

def process_image(image, user, request, latitude, longitude):
    detection_date = request.form.get('detection_date')
    date_string = detection_date.strip('"')
    detection_date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    filename = image.filename
    image_path = f"{raw_images_dir}/{filename}"
    image.save(image_path)

    raw_image = image_path
    detect(raw_image, yoloModel)
    # os.remove(raw_image)
    json_data = Predict(model, images_folder)

    if json_data:

        if is_near_existing_garbage(latitude, longitude):
            print("Detected garbage is within 15 meters of existing garbage. Skipping creation.")
            MoveAndDel(images_folder, destination_folder, labels_folder, json_data)
            print("Processing complete.")
            os.remove(raw_image)
            #new
            clear_folder(destination_folder) 
            return

        detector = Detector.query.filter_by(id=user.id).first()
        if detector:
            detector.score += 1
            db.session.commit()

        volume = determine_volume(json_data)
        new_garbage = Garbage(
            latitude=latitude,
            longitude=longitude,
            owner=user.id,
            detection_date=detection_date,
            volume=volume,
            img=filename
        )
        db.session.add(new_garbage)
        db.session.commit()
        print("Garbage object created successfully.")
    else:
        os.remove(raw_image)    

    MoveAndDel(images_folder, destination_folder, labels_folder, json_data)
    clear_folder(destination_folder)
    print("Processing complete.")

#delete content inside finished folder 
def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def determine_volume(json_data):
    # Determine the volume based on the entries in the JSON data
    sizes = [entry['size'] for entry in json_data]
    if 'large' in sizes:
        return 'large'
    else:
        return 'small'
