from fastapi import APIRouter, Query, File, UploadFile, Form, WebSocket
from fastapi.responses import JSONResponse
from app.database.faces import get_all_face_embeddings
from app.database.images import get_path_from_id
from app.facecluster.init_face_cluster import get_face_cluster
from app.facenet.preprocess import cosine_similarity
from app.utils.path_id_mapping import get_id_from_path
from app.facenet.facenet import extract_face_embeddings, detect_faces
from app.yolov8.YOLOv8 import YOLOv8
from app.config.settings import DEFAULT_FACE_DETECTION_MODEL
import os
import tempfile
import uuid
import cv2
import base64
import json
import asyncio

webcam_locks = {}

router = APIRouter()


@router.get("/match")
def face_matching():
    try:
        all_embeddings = get_all_face_embeddings()

        similar_pairs = []

        for i, img1_data in enumerate(all_embeddings):
            for j, img2_data in enumerate(all_embeddings):
                if i >= j:
                    continue

                for embedding1 in img1_data["embeddings"]:
                    for embedding2 in img2_data["embeddings"]:
                        similarity = cosine_similarity(embedding1, embedding2)
                        if similarity >= 0.5:
                            img1 = img1_data["image_path"].split("/")[-1]
                            img2 = img2_data["image_path"].split("/")[-1]
                            similar_pairs.append(
                                {
                                    "image1": img1,
                                    "image2": img2,
                                    "similarity": float(similarity),
                                }
                            )
                            break
                    else:
                        continue
                    break

        return JSONResponse(
            status_code=200,
            content={
                "data": {"similar_pairs": similar_pairs},
                "message": "Successfully matched face embeddings",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )


@router.get("/clusters")
def face_clusters():
    try:
        cluster = get_face_cluster()
        raw_clusters = cluster.get_clusters()

        # Convert image IDs to paths
        formatted_clusters = {}
        for cluster_id, image_ids in raw_clusters.items():
            formatted_clusters[int(cluster_id)] = [
                get_path_from_id(image_id) for image_id in image_ids
            ]

        return JSONResponse(
            status_code=200,
            content={
                "data": {"clusters": formatted_clusters},
                "message": "Successfully retrieved face clusters",
                "success": True
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )


@router.get("/related-images")
def get_related_images(path: str = Query(..., description="full path to the image")):
    try:
        cluster = get_face_cluster()
        image_id = get_id_from_path(path)
        related_image_ids = cluster.get_related_images(image_id)
        related_image_paths = [get_path_from_id(
            id) for id in related_image_ids]

        return JSONResponse(
            status_code=200,
            content={
                "data": {"related_images": related_image_paths},
                "message": f"Successfully retrieved related images for {path}",
                "success": True
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )


async def process_face_search(image_path, threshold=0.5):
    try:
        query_embeddings = extract_face_embeddings(image_path)

        if query_embeddings == "no_person":
            return False, None, "No person detected in the image"

        if not query_embeddings or len(query_embeddings) == 0:
            return False, None, "No faces detected in the image"

        all_embeddings = get_all_face_embeddings()

        if not all_embeddings:
            return True, {"matches": [], "count": 0}, "No face embeddings found in the database"

        matches = []
        for db_face in all_embeddings:
            image_path = db_face["image_path"]
            db_embeddings = db_face["embeddings"]

            max_similarity = 0
            for query_face in query_embeddings:
                for db_face_emb in db_embeddings:
                    similarity = cosine_similarity(query_face, db_face_emb)
                    max_similarity = max(max_similarity, similarity)

            if max_similarity >= threshold:
                matches.append({
                    "path": image_path,
                    "similarity": float(max_similarity)
                })

        matches.sort(key=lambda x: x["similarity"], reverse=True)

        return True, {"matches": matches, "count": len(matches)}, None

    except Exception as e:
        return False, None, str(e)


@router.post("/search-by-face")
async def search_by_face(
    file: UploadFile = File(...),
    threshold: float = Form(0.6)
):
    temp_file_path = os.path.join(tempfile.gettempdir(
    ), f"{uuid.uuid4()}{os.path.splitext(file.filename or '.jpg')[1]}")

    try:
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        success, result_data, error_message = await process_face_search(temp_file_path, threshold)

        if not success:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "No faces detected",
                    "message": error_message
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "data": result_data,
                "message": f"Found {result_data['count']} images with similar faces",
                "success": True
            }
        )

    except Exception as e:
        import traceback
        print(f"Error in search-by-face: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "message": str(e)
            }
        )
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.websocket("/webcam-feed/{client_id}")
async def webcam_feed(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f"WebSocket connection accepted for client: {client_id}")
    webcam_feed.last_time = 0

    # Check if the camera is already in use.
    if client_id in webcam_locks:
        print(f"Camera already in use by client: {client_id}")
        try:
            await websocket.send_json({"event": "error", "message": "Camera already in use"})
            await websocket.close()
        except Exception as e:
            print(f"Error sending 'camera in use' message: {e}")
        return

    # Lock the camera.
    webcam_locks[client_id] = True
    cap = None
    camera_opened = False

    try:
        # Try to open the camera.
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                for camera_index in range(3):
                    print(f"Trying to open camera at index {camera_index}")
                    # Make sure any previous attempts are released first
                    if cap:
                        cap.release()
                        cap = None

                    cap = cv2.VideoCapture(camera_index)
                    if cap and cap.isOpened():
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        cap.set(cv2.CAP_PROP_FPS, 30)

                        ret, test_frame = cap.read()
                        if not ret:
                            print(
                                f"Camera at index {camera_index} opened but read failed")
                            cap.release()
                            cap = None
                            continue

                        print(
                            f"Successfully opened camera at index {camera_index}")
                        camera_opened = True
                        break
                    else:
                        print(f"Failed to open camera at index {camera_index}")
                        if cap:
                            cap.release()
                            cap = None

                if camera_opened:
                    break

                print(
                    f"Camera open attempt {attempt+1} failed, waiting before retry")
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error opening camera (attempt {attempt+1}): {e}")
                if cap:
                    cap.release()
                    cap = None
                await asyncio.sleep(1)

        # Check if camera is successfully opened
        if not camera_opened or not cap or not cap.isOpened():
            print("Could not open any webcam")
            try:
                await websocket.send_json({"event": "error", "message": "Could not open webcam"})
            except Exception as e:
                print(f"Error sending 'could not open webcam' message: {e}")

            # Remove lock if failed
            if client_id in webcam_locks:
                del webcam_locks[client_id]

            try:
                await websocket.close()
            except Exception as e:
                print(f"Error closing websocket: {e}")
            return

        # Initialize YOLO Model
        yolov8_detector = YOLOv8(
            DEFAULT_FACE_DETECTION_MODEL, conf_thres=0.3, iou_thres=0.3)
        print(f"Sending connected event to client {client_id}")

        try:
            await websocket.send_json({"event": "connected", "message": "Camera connected successfully"})
            print(f"Connected event sent to client {client_id}")
        except Exception as e:
            print(f"Error sending connected message: {e}")
            # if Client disconnected, exit
            if cap:
                cap.release()
            if client_id in webcam_locks:
                del webcam_locks[client_id]
            return

        # loop for processing frames
        while True:
            try:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                    command = json.loads(data)

                    if command.get("action") == "close":
                        print(
                            f"Client {client_id} requested to close connection")
                        break

                    elif command.get("action") == "capture":
                        success, frame = cap.read()
                        if success:
                            # Save the captured frame to a temp file
                            temp_file_path = os.path.join(
                                tempfile.gettempdir(), f"webcam_capture_{uuid.uuid4()}.jpg")
                            cv2.imwrite(temp_file_path, frame)

                            try:
                                success, result_data, error_message = await process_face_search(temp_file_path)

                                if not success:
                                    await websocket.send_json({
                                        "event": "search_result",
                                        "success": False,
                                        "message": error_message
                                    })
                                else:
                                    # Send results back to client
                                    await websocket.send_json({
                                        "event": "search_result",
                                        "success": True,
                                        "matches": result_data["matches"]
                                    })

                            except Exception as e:
                                print(f"Error processing capture: {e}")
                                try:
                                    await websocket.send_json({
                                        "event": "search_result",
                                        "success": False,
                                        "message": f"Error processing capture: {str(e)}"
                                    })
                                except Exception as e:
                                    print(
                                        f"Error sending capture error response: {e}")

                            finally:
                                # Clean up temp file
                                if os.path.exists(temp_file_path):
                                    os.remove(temp_file_path)

                        else:
                            try:
                                await websocket.send_json({
                                    "event": "search_result",
                                    "success": False,
                                    "message": "Failed to capture frame"
                                })
                            except Exception as e:
                                print(
                                    f"Error sending capture failure response: {e}")

                except asyncio.TimeoutError:
                    # Prevents crashing while waiting for messages
                    pass
                except Exception as e:
                    print(f"Error processing message: {e}")
                    break

                success, frame = cap.read()
                if not success:
                    print("Failed to read frame")
                    await asyncio.sleep(0.1)
                    continue

                # Process frame and detect faces
                results = yolov8_detector(frame)
                boxes, scores, class_ids = results

                # Draw boxes for visualization
                faces_detected = 0
                for box, score in zip(boxes, scores):
                    if score > 0.5:
                        faces_detected += 1
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(frame, (x1, y1),
                                      (x2, y2), (0, 255, 0), 2)

                current_time = cv2.getTickCount()
                fps = None
                if hasattr(webcam_feed, 'last_time'):
                    fps = cv2.getTickFrequency() / (current_time - webcam_feed.last_time)
                webcam_feed.last_time = current_time

                # Send frame to client
                try:
                    ret, buffer = cv2.imencode(
                        '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if not ret:
                        print("Failed to encode frame")
                        continue

                    frame_data = base64.b64encode(buffer).decode('utf-8')
                    await websocket.send_json({
                        "event": "frame",
                        "image": frame_data,
                        "faces_detected": faces_detected,
                        "fps": round(fps) if fps else None
                    })

                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break

            except Exception as e:
                print(f"Error in main loop: {e}")
                break

    except Exception as e:
        print(f"Webcam error for client {client_id}:")

    finally:
        print(f"Cleaning up resources for client {client_id}")
        if cap:
            cap.release()

        if client_id in webcam_locks:
            del webcam_locks[client_id]
            print(f"Removed camera lock for client {client_id}")
