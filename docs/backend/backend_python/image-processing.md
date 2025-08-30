# Image Processing

We use `asyncio` for processing multiple images at the same time in the background without blocking the frontend, this can be found in
`app/routes/images.py`.

PictoPy uses different models for achieving its tagging capabilities.
The discussed models below are default models, you can change them by going to `app/models` directory and change the paths in the configuration files.

## Object Detection with YOLOv8

We use YOLOv8 to spot objects in your photos. Here's what it does:

YOLOv8 takes your image and runs it through its model. It figures out what objects are in the image and where they are.
The result is a list of objects, their locations, and how confident the model is about each detection. If a `person` class is predicted we pass it on
to the face detection model which we discuss in the next section.

???+ tip "Fun Fact"
YOLO stands for "You Only Look Once". We use the model provided by [Ultralytics](https://github.com/ultralytics/ultralytics) by default.

## Face Detection and Recognition

For faces, we do a bit more:

We start with a special version of YOLOv8 that's really good at finding faces. Once we find a face, we zoom in on it
(by cropping it to `160x160` - the shape FaceNet expects) and pass it to our FaceNet model.
FaceNet then creates a unique 'embedding' for each face, the representation of of the face in a form of numbers.

???+ tip "Fun Fact"
We use another YOLOv8 model for this as well by default. This was pretrained on top of the one provided by Ultralytics and is called
[yolov8-face](https://github.com/akanametov/yolo-face)

???+ note "What's an embedding?"
An embedding is a bunch of numbers that represent the face. Similar faces will have similar numbers. FaceNet creates a 512 embedding array
if an image has

## Face Clustering

Now, here's where it gets interesting:

We use something called DBSCAN to group similar faces together. This process happens automatically as you add new photos to the system, we perform reclustering
after every 5 photos are added (this can be changed in the code) but apart from that, the photos are assigned a cluster based on the embedding distance
of the faces in the photo with the mean of each of the clusters.

## How It All Fits Together

When you add a new photo, we first look for objects and faces. If we find faces, we generate embeddings for them. These embeddings then get added to our face clusters.
All this information gets stored in our database so we can find it later.

## Under the Hood

We're using ONNX runtime to run our AI models quickly. Everything's stored in SQLite databases, making it easy to manage.
The system updates clusters as you add or remove photos, so it keeps getting smarter over time.

## PictoPy Model Parameters

Here are some key parameters for the main models used in PictoPy's image processing pipeline.

### YOLOv8 Object Detection

| Parameter    | Value    | Description                                     |
| ------------ | -------- | ----------------------------------------------- |
| `conf_thres` | 0.7      | Confidence threshold for object detection       |
| `iou_thres`  | 0.5      | IoU (Intersection over Union) threshold for NMS |
| Input Shape  | Varies   | Determined dynamically from the model           |
| Output       | Multiple | Includes bounding boxes, scores, and class IDs  |

### Face Detection (YOLOv8 variant)

| Parameter    | Value                          | Description                             |
| ------------ | ------------------------------ | --------------------------------------- |
| `conf_thres` | 0.2                            | Confidence threshold for face detection |
| `iou_thres`  | 0.3                            | IoU threshold for NMS in face detection |
| Model Path   | `DEFAULT_FACE_DETECTION_MODEL` | Path to the face detection model file   |

### FaceNet (Face Recognition)

| Parameter   | Value                   | Description                          |
| ----------- | ----------------------- | ------------------------------------ |
| Model Path  | `DEFAULT_FACENET_MODEL` | Path to the FaceNet model file       |
| Input Shape | (1, 3, 160, 160)        | Expected input shape for face images |
| Output      | 512-dimensional vector  | Face embedding dimension             |

### Face Clustering (DBSCAN)

| Parameter     | Value    | Description                                                                                |
| ------------- | -------- | ------------------------------------------------------------------------------------------ |
| `eps`         | 0.3      | Maximum distance between two samples for them to be considered as in the same neighborhood |
| `min_samples` | 2        | Number of samples in a neighborhood for a point to be considered as a core point           |
| `metric`      | "cosine" | Distance metric used for clustering                                                        |

Note: Some of these values are default parameters and can be adjusted when initializing the models or during runtime, depending on the specific use case or performance requirements.
