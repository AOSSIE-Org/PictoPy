from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
import asyncio
from PIL import Image
from app.utils.classification import get_classes
from app.routes.images import get_all_image_paths,delete_image_db
from app.database.folders import get_all_folders,get_folder_id_from_path
from app.config.settings import THUMBNAIL_IMAGES_PATH
from app.facenet.facenet import detect_faces
from app.database.images import (
    insert_image_db,
    extract_metadata,
)
from app.database.folders import (
    delete_folder,
    get_all_folders
)


async def process_images(tasks):
    await asyncio.gather(*tasks)

async def run_get_classes(img_path,folder_id=None):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    insert_image_db(img_path, result, extract_metadata(img_path),folder_id)
    if result:
        classes = result.split(",")
        if "0" in classes and classes.count("0") < 8:
            detect_faces(img_path)


# Handles Random works done by user
async def my_scheduled_task():
    print("Running scheduled task at:", time.strftime("%Y-%m-%d %H:%M:%S"))
    try : 
        folder_paths = get_all_folders()
        image_file_paths = get_all_image_paths()
        file_dict = {}
        curr_files = []
        for folder_path in folder_paths : 
            file_dict[folder_path] = get_folder_id_from_path(folder_path=folder_path)
            curr_files += [os.path.join(folder_path, file) for file in os.listdir(folder_path)]
        
            
        image_file_paths = set(image_file_paths)
        curr_files = set(curr_files)

        need_to_delete_files = image_file_paths.difference(curr_files)
        need_to_add_files = curr_files.difference(image_file_paths)

        image_extensions = ["jpg", "jpeg", "png", "bmp", "gif"]
        tasks = []

        # Addding New Images to AI Tagging 

        print("Preprocessing Started for adding files ... ")
        for file_path in need_to_add_files:
            
            folder_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_extension = str(file_path).split('.').pop()
            thumbnail_path = f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}"

            # Generate thumbnail image 
            img = Image.open(file_path)
            img.thumbnail((400, 400))
            img.save(thumbnail_path)

            folder_id = file_dict[folder_path]
            if file_extension in image_extensions:
                tasks.append(asyncio.create_task(run_get_classes(file_path, folder_id=folder_id)))

        print("Tasks = ",tasks)
        await asyncio.create_task(process_images(tasks))

        # Removing deleted images path from Database
        
        if len(need_to_delete_files) : 
            for file_path in need_to_delete_files : 
                file_name = os.path.basename(file_path)
                os.remove(f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}")
                delete_image_db(file_path)

        # Removing Deleted Folders from Database 
        folders = get_all_folders()
        for folder in folders : 
            if not os.path.exists(folder) : 
                delete_folder(folder_path=folder)



    except Exception as e : 
        print("Exception Occured in Scheduler")
        

def run_async_task():
    """ Helper function to run the async scheduled task inside APScheduler """
    asyncio.run(my_scheduled_task())


scheduler = BackgroundScheduler()
scheduler.add_job(run_async_task, "interval", seconds=5)

def start_scheduler():
    scheduler.start()
