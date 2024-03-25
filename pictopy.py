import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2

class PictoPyApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PictoPy")
        
        # Create and pack the open image button
        self.open_button = tk.Button(master, text="Open Image", command=self.open_image)
        self.open_button.pack(pady=10)
        
        # Label to display the file path of the selected image
        self.file_path_label = tk.Label(master, text="No image selected.")
        self.file_path_label.pack(pady=5)
        
        # Canvas to display the selected image
        self.canvas = tk.Canvas(master, width=400, height=300)
        self.canvas.pack(pady=10)
        
        # Label to display detected objects
        self.objects_label = tk.Label(master, text="")
        self.objects_label.pack(pady=5)
        
        # Create a quit button
        self.quit_button = tk.Button(master, text="Quit", command=master.quit)
        self.quit_button.pack(pady=10)
    
    def open_image(self):
        # Open a file dialog to select an image
        file_path = filedialog.askopenfilename()
        
        if file_path:
            # Display the file path of the selected image
            self.file_path_label.config(text="Selected Image: " + file_path)
            
            # Process the selected image
            self.process_image(file_path)
    
    def process_image(self, file_path):
        # Load the image
        image = cv2.imread(file_path)
        
        # Convert image from BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize image to fit in the canvas
        image = cv2.resize(image, (400, 300))
        
        # Convert image to PIL format
        image = Image.fromarray(image)
        
        # Convert PIL image to ImageTk format
        image_tk = ImageTk.PhotoImage(image)
        
        # Display the image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
        self.canvas.image = image_tk
        
        # Perform dummy object recognition
        objects_detected = ['person', 'dog', 'cat']  # Dummy example
        
        # Display detected objects
        self.objects_label.config(text="Detected Objects: " + ', '.join(objects_detected))

def main():
    root = tk.Tk()
    app = PictoPyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
