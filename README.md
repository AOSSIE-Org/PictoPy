# Pictopy

Pictopy is an open-source image sorting tool designed to efficiently organize your image collection.

## Features Implemented

1. **Dedicated Local Database:**

   - Utilizes a dedicated local database for caching tags, enhancing the speed and efficiency of image sorting operations.

2. **Advanced Image Recognition:**

   - Employs an advanced image recognition library capable of evaluating objects within images, including facial recognition, leading to a smoother and more accurate sorting process.

3. **Improved UI/UX:**

   - Offers a refined user interface for a more intuitive and enjoyable user experience.

4. **Multiprocessing Support:**
   - Pictopy now supports multiprocessing, optimizing the sorting process and enhancing overall performance.

## Installation

To install dependencies, run the following command:

```
pip install PyQt5
```

## How to Run

Follow these steps to run Pictopy:

1. Clone the repository to your local machine.
2. Install PyQt by running the following command:
   ```
   pip install PyQt5
   ```
3. Navigate to the project directory and run the following command to start the app:
   ```
   python app.py
   ```

### Additional Steps for Running Electron UI:

If you prefer to use the Electron UI, follow these additional steps:

1. Copy the contents of the UI folder to the project directory.
2. Initialize npm by running:
   ```
   npm init -y
   ```
3. Install Electron as a development dependency:
   ```
   npm install electron --save-dev
   ```
4. Modify the "scripts" section in the package.json file as follows:
   ```json
   "scripts": {
       "start": "electron ."
   }
   ```
5. Finally, run the application using the following command:
   ```
   npm start
   ```

Now you can enjoy sorting your images efficiently with Pictopy!
