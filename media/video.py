import cv2
from yolov8 import detectClasses
from typing import Generator, Tuple, Set

def extractFrames(inputPath: str, skip: int = 50) -> Generator[bytes, None, None]:
    """
    Extract frames from a video file.

    Args:
    - inputPath: Path to the input video file.
    - skip: Number of frames to skip between extracted frames (default is 6).

    Returns:
    - Generator: Yields frames from the video file.
    """
    cap = cv2.VideoCapture(inputPath)
    frameCount = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frameCount % skip == 0:
            yield frame
        frameCount += 1
    cap.release()

def processFrames(frames: Generator, modelPath: str) -> Generator[Tuple[str, bytes], None, None]:
    """
    Process frames using a detection model.

    Args:
    - frames: Generator yielding frames.
    - modelPath: Path to the detection model.

    Yields:
    - Generator: Yields detected classes for each frame.
    """
    for frame in frames:
        yield detectClasses(frame, modelPath)

def saveVideo(outputPath: str, frames: Generator, fps: float, frameSize: Tuple[int, int]) -> None:
    """
    Save frames as a video file.

    Args:
    - outputPath: Path to save the output video file.
    - frames: Generator yielding frames to save.
    - fps: Frames per second (FPS) of the output video.
    - frameSize: Size of each frame (width, height).
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(outputPath, fourcc, fps, frameSize)
    for frame in frames:
        out.write(frame)
    out.release()

def videoClasses(inputPath: str, modelPath: str, outputPath: str = None) -> Set[str]:
    """
    Extract and save video classes.

    Args:
    - inputPath: Path to the input video file.
    - modelPath: Path to the detection model.
    - outputPath: Optional path to save the output video file.

    Returns:
    - Set[str]: Set of unique classes detected across all frames.
    """
    frames = extractFrames(inputPath)
    fps = cv2.VideoCapture(inputPath).get(cv2.CAP_PROP_FPS)
    firstFrameClasses, firstFrame = next(processFrames(frames, modelPath))

    def combinedFrames() -> Generator[bytes, None, None]:
        yield firstFrame
        for _, frame in processFrames(frames, modelPath):
            yield frame

    if outputPath:
        height, width, _ = firstFrame.shape
        frameSize = (width, height)

        # Save the first frame and the rest of the processed frames
        saveVideo(outputPath, combinedFrames(), fps, frameSize)

    # Collect and return combined classes from each frame of the video
    allClasses = set(firstFrameClasses)
    for classes, _ in processFrames(frames, modelPath):
        allClasses.update(classes)
    
    return allClasses

def getThumbnail(inputPath: str) -> bytes:
    """
    Get a single frame from the video and return it as a thumbnail.

    Args:
    - inputPath: Path to the input video file.

    Returns:
    - bytes: Thumbnail image in bytes format.
    """
    cap = cv2.VideoCapture(inputPath)
    
    # Ensure the video was opened successfully
    if not cap.isOpened():
        raise ValueError("Unable to open the video file.")
    
    # Read the first frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError("Unable to read the video file.")

    # Encode the frame to JPEG format
    success, encodedImage = cv2.imencode('.jpg', frame)
    
    if not success:
        raise ValueError("Failed to encode the image.")

    # Convert the encoded image to bytes
    thumbnailBytes = encodedImage.tobytes()

    return thumbnailBytes