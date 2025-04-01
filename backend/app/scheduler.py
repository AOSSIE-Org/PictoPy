from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
import asyncio
from typing import Any, List, Optional, Dict, Set
from PIL import Image
from app.utils.classification import get_classes
from app.routes.images import get_all_image_paths, delete_image_db
from app.database.folders import get_all_folders, get_folder_id_from_path
from app.config.settings import THUMBNAIL_IMAGES_PATH
from app.facenet.facenet import detect_faces
from app.database.images import insert_image_db
from app.utils.metadata import extract_metadata
from app.database.folders import delete_folder


async def process_images(tasks: List[asyncio.Task[Any]]) -> None:
    await asyncio.gather(*tasks)


async def run_get_classes(img_path: str, folder_id: Optional[str] = None) -> None:
    loop = asyncio.get_event_loop()
    result: Optional[str] = await loop.run_in_executor(None, get_classes, img_path)
    insert_image_db(img_path, result, extract_metadata(img_path), folder_id)

    if result:
        classes = result.split(",")
        if "0" in classes and classes.count("0") < 8:
            detect_faces(img_path)


async def my_scheduled_task() -> None:
    try:
        print("Running scheduled task at:", time.strftime("%Y-%m-%d %H:%M:%S"))

        folder_paths: List[str] = get_all_folders()
        image_file_paths: Set[str] = set(get_all_image_paths())  # Ensure it's a set

        file_dict: Dict[str, Optional[str]] = {}
        curr_files: Set[str] = set()  # Ensure it's a set

        for folder_path in folder_paths:
            file_dict[folder_path] = str(
                get_folder_id_from_path(folder_path=folder_path)
            )
            curr_files.update(
                os.path.join(folder_path, file) for file in os.listdir(folder_path)
            )

        # Finding files to delete and add
        need_to_delete_files: Set[str] = image_file_paths.difference(curr_files)
        need_to_add_files: Set[str] = curr_files.difference(image_file_paths)

        image_extensions = {"jpg", "jpeg", "png", "bmp", "gif"}
        tasks: List[asyncio.Task[Any]] = []

        # Add newly added images for AI tagging
        for file_path in need_to_add_files:
            folder_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_extension = str(file_path).split(".").pop()

            if file_extension not in image_extensions:
                continue

            thumbnail_path = f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}"
            img = Image.open(file_path)
            img.thumbnail((400, 400))
            img.save(thumbnail_path)

            folder_id = file_dict[folder_path]
            tasks.append(
                asyncio.create_task(run_get_classes(file_path, folder_id=folder_id))
            )

        await process_images(tasks)

        # Removing deleted images from database
        if need_to_delete_files:
            for file_path in need_to_delete_files:
                file_name = os.path.basename(file_path)
                thumbnail_path = (
                    f"{THUMBNAIL_IMAGES_PATH}/PictoPy.thumbnails/{file_name}"
                )
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                delete_image_db(file_path)

        # Removing deleted folders from database
        folders: List[str] = get_all_folders()
        for folder in folders:
            if not os.path.exists(folder):
                delete_folder(folder_path=folder)

    except Exception as e:
        print(f"Exception Occurred in Scheduler: {e}")


def run_async_task() -> None:
    asyncio.run(my_scheduled_task())


def start_scheduler() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_async_task, "interval", minutes=15)
    scheduler.start()
