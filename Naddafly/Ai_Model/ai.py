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


raw_images_dir = 'Naddafly/Ai_Model/images'


def process_image(image, user, request):
    # for image_file in os.listdir(raw_images_dir):
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    # owner_id = request.form.get('owner_id')  # Assuming this is the ID of the user who owns the garbage
    detection_date = request.form.get('detection_date')
    detection_date = datetime.strptime(detection_date, '%Y-%m-%d %H:%M:%S')
    filename = image.filename
    image_path = f"{raw_images_dir}/{filename}"
    image.save(image_path)
    for image_file in os.listdir(raw_images_dir):
        if image_file.endswith('.jpg') or image_file.endswith('.jpeg') or image_file.endswith('.png'):
            # Perform detection on the image
            raw_image = os.path.join(raw_images_dir, image_file)
            detect(raw_image, yoloModel)
            os.remove(raw_image)
            json_data = Predict(model, images_folder)
            if json_data:

                detector = Detector.query.filter_by(id=user.id).first()
                if detector:
                    # Increment the score of the detector
                    detector.score += 1
                    db.session.commit()
                print(json_data[0]['size'])
                new_garbage = Garbage(
                    latitude=latitude,
                    longitude=longitude,
                    owner=user.id,
                    detection_date=detection_date,
                    volume=json_data[0]['size']
                )
                db.session.add(new_garbage)
                db.session.commit()
                print("Garbage object created successfully.")
            ##heare

            print(json_data)
            MoveAndDel(images_folder, destination_folder, labels_folder, json_data)

    print("Processing complete.")
