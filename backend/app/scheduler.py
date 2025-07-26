from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
import asyncio
from PIL import Image
from app.utils.classification import get_classes
from app.routes.images import get_all_image_paths, delete_image_db
from app.database.folders import get_all_folders, get_folder_id_from_path
from app.config.settings import THUMBNAIL_IMAGES_PATH
from app.facenet.facenet import detect_faces
from app.database.images import insert_image_db
from app.utils.metadata import extract_metadata
from app.database.folders import delete_folder


async def process_images(tasks):
    """
    Asynchronously waits for all the given tasks to complete.
    Args:
        tasks (list): List of asyncio tasks to be processed.
    """
    await asyncio.gather(*tasks)


async def run_get_classes(img_path, folder_id=None):
    """
    Runs image classification in a thread pool executor to avoid blocking the event loop.
    Inserts image data and metadata into the database.
    Additionally detects faces if certain conditions are met.
    
    Args:
        img_path (str): Path of the image to classify.
        folder_id (int, optional): ID of the folder containing the image.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    insert_image_db(img_path, result, extract_metadata(img_path), folder_id)
    if result:
        classes = result.split(",")
        # If class "0" appears but less than 8 times, run face detection
        if "0" in classes and classes.count("0") < 8:
            detect_faces(img_path)


async def my_scheduled_task():
    """
    Main scheduled task that:
    - Retrieves all folder and image paths.
    - Compares files in the filesystem with those recorded in the database.
    - Adds new images for classification and thumbnail creation.
    - Deletes thumbnails and database entries for removed images.
    - Deletes database records for folders no longer existing on disk.
    Runs every 15 minutes as scheduled.
    """
    try:
        print("Running scheduled task at:", time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Get all folders and image paths from the database
        folder_paths = get_all_folders()
        image_file_paths = get_all_image_paths()
        
        file_dict = {}
        curr_files = []
        
        # For each folder, get its folder_id and current files within it
        for folder_path in folder_paths:
            file_dict[folder_path] = get_folder_id_from_path(folder_path=folder_path)
            curr_files += [
                os.path.join(folder_path, file) for file in os.listdir(folder_path)
            ]

        image_file_paths = set(image_file_paths)
        curr_files = set(curr_files)

        # Determine which files are deleted or newly added by comparing DB vs filesystem
        need_to_delete_files = image_file_paths.difference(curr_files)
        need_to_add_files = curr_files.difference(image_file_paths)

        image_extensions = ["jpg", "jpeg", "png", "bmp", "gif"]
        tasks = []

        # Process newly added images: create thumbnails, classify and insert into DB
        for file_path in need_to_add_files:
            folder_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_extension = str(file_path).split(".").pop()

            if file_extension not in image_extensions:  # Skip non-image files
                continue

            thumbnail_path = f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}"
            img = Image.open(file_path)
            img.thumbnail((400, 400))
            img.save(thumbnail_path)

            folder_id = file_dict[folder_path]
            if file_extension in image_extensions:
                tasks.append(
                    asyncio.create_task(run_get_classes(file_path, folder_id=folder_id))
                )

        # Wait for all classification tasks to complete
        await asyncio.create_task(process_images(tasks))

        # Remove thumbnails and DB entries for images deleted from filesystem
        if need_to_delete_files:
            for file_path in need_to_delete_files:
                file_name = os.path.basename(file_path)
                os.remove(f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}")
                delete_image_db(file_path)

        # Remove database entries for folders no longer existing on disk
        folders = get_all_folders()
        for folder in folders:
            if not os.path.exists(folder):
                delete_folder(folder_path=folder)

    except Exception as e:
        print(f"Exception Occurred in Scheduler: {e}")


def run_async_task():
    """
    Helper function to run the async scheduled task synchronously,
    required for APScheduler compatibility.
    """
    asyncio.run(my_scheduled_task())


def start_scheduler():
    """
    Initializes and starts a background scheduler that runs
    'run_async_task' every 15 minutes.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_async_task, "interval", minutes=15)
    scheduler.start()
