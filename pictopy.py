import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2

class PictoPyApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PictoPy")
        
        self.open_button = tk.Button(master, text="Open Image", command=self.open_image)
        self.open_button.pack(pady=10)
        
        self.file_path_label = tk.Label(master, text="No image selected.")
        self.file_path_label.pack(pady=5)
        
        # Canvas to display the selected image
        self.canvas = tk.Canvas(master, width=400, height=300)
        self.canvas.pack(pady=10)
        
        self.objects_label = tk.Label(master, text="")
        self.objects_label.pack(pady=5)
        
    
    def open_image(self):
        file_path = filedialog.askopenfilename()
        
        if file_path:
            self.file_path_label.config(text="Selected Image: " + file_path)
            
            self.process_image(file_path)
    
    def process_image(self, file_path):
        image = cv2.imread(file_path)
        
        
        image = Image.fromarray(image)
        
        image_tk = ImageTk.PhotoImage(image)
        
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
        self.canvas.image = image_tk
        
        # Perform dummy object recognition
        objects_detected = ['person']  # Dummy example
        
        # Display detected objects
        self.objects_label.config(text="Detected Objects: " + ', '.join(objects_detected))

def main():
    root = tk.Tk()
    app = PictoPyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
