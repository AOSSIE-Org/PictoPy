# Contents
1. [`Backend`](#Backend)
2. [`Project Description (PictoPy)`](#PictoPy)

# Backend
## Steps to run backend

1. Head over to `/backend` after cloning
2. Create a virtual env by running: `python3 -m venv venv`
3. Activate the env by running `source venv/bin/activate` and install dependancies via `pip install requirments.txt`
4. Start the server via `./run.sh` (for development mode add the flag  `--test` [RECOMMENDED])
5. The server should now be hosted on port `8000` on localhost.

## Some pointers for the backend

- Entry point is `main.py` which calls the routes, currently there is a `/test` route for developing, to test an image, send a request to the backend (`localhost:8000/test/return`) with the following Body format:
```
{
  "path": "<Path to image>"
}
```
Eg: try it out with path as`backend/tests/inputs/zidane.jpg`
- A window should pop up showing the highlighted detections, simply press `q` to exit, or comment out the `cv2` lines in `test.py`
- Change the type of inference by changing `model_path` variable in `app/test` route, by default there are two models available in the `app/models` directory (face and object deteciton).
# PictoPy

An open source image sorting tool designed to organize your image collection efficiently.


how to run 

npm install 
npm start    
