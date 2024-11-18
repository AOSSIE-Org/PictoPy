import os
import sqlite3
import numpy as np
from PIL import Image
from app.image_captioning.caption import caption1
from app.config.settings import IMAGES_DATABASE_PATH


def captioning_images():
    conn = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT path FROM image_id_mapping;")
    paths = [row[0] for row in cursor.fetchall()]  
    
    conn.close()
    captions = []
    for i in paths:
        img = Image.open(os.path.abspath(i))  
        img = np.array(img) 
        caption = caption1(img)
        print(f"{os.path.abspath(i)}:{caption}")
        captions.append(caption)
    print(captions)
    print(paths)

captioning_images()    