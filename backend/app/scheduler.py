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
    await asyncio.gather(*tasks)


async def run_get_classes(img_path, folder_id=None):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_classes, img_path)
    insert_image_db(img_path, result, extract_metadata(img_path), folder_id)
    if result:
        classes = result.split(",")
        if "0" in classes and classes.count("0") < 8:
            detect_faces(img_path)


async def my_scheduled_task():
    try:
        print("Running scheduled task at:", time.strftime("%Y-%m-%d %H:%M:%S"))
        folder_paths = get_all_folders()
        image_file_paths = get_all_image_paths()
        file_dict = {}
        curr_files = []
        for folder_path in folder_paths:
            file_dict[folder_path] = get_folder_id_from_path(
                folder_path=folder_path
            )  # Storing folder_id for efficient accessing
            curr_files += [
                os.path.join(folder_path, file) for file in os.listdir(folder_path)
            ]  # Adding all files in the current folder

        image_file_paths = set(image_file_paths)
        curr_files = set(curr_files)

        need_to_delete_files = image_file_paths.difference(
            curr_files
        )  # {Image Paths Exists in Database} \ {curr_files}
        need_to_add_files = curr_files.difference(
            image_file_paths
        )  # {curr_files} \ {Image Paths Exists in Database}

        image_extensions = ["jpg", "jpeg", "png", "bmp", "gif"]
        tasks = []

        # Addding Newly added Images to AI Tagging

        for file_path in need_to_add_files:
            folder_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_extension = str(file_path).split(".").pop()

            if file_extension not in image_extensions:  # Checking Image or not
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

        await asyncio.create_task(process_images(tasks))

        # Removing deleted images path from Database

        if need_to_delete_files:
            for file_path in need_to_delete_files:
                file_name = os.path.basename(file_path)
                os.remove(f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}")
                delete_image_db(file_path)

        # Removing Deleted Folders from Database

        folders = get_all_folders()
        for folder in folders:
            if not os.path.exists(folder):
                delete_folder(folder_path=folder)

    except Exception as e:
        print(f"Exception Occurred in Scheduler: {e}")


def run_async_task():
    asyncio.run(my_scheduled_task())


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_async_task, "interval", minutes=15)
    scheduler.start()