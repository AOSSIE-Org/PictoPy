from torchvision import models
import torch
from torchvision import transforms
import json
import tkinter as tk
from PIL import ImageTk, Image
from tkinter import filedialog

# https://pytorch.org/hub/pytorch_vision_alexnet/
# https://github.com/iAnkeet/Machine-Learning-Tkinter-GUI/blob/master/gui-ml.py


def load_img():
    global img, image
    for img_display in frame.winfo_children():
        img_display.destroy()

    image = filedialog.askopenfilename(initialdir="/", title="Choose an image",
                                       filetypes=(("all files", "*.*"), ("png files", "*.png")))
    basewidth = 150
    img = Image.open(image)
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    file_name = image.split('/')
    panel = tk.Label(frame, text= str(file_name[len(file_name)-1]).upper()).pack()
    panel_image = tk.Label(frame, image=img).pack()


def classify():
    img_t = transform(Image.open(image))
    sample = torch.unsqueeze(img_t, 0)
    data = alexnet(sample)
    _, indices = torch.sort(data, descending=True)
    percentage = torch.nn.functional.softmax(data, dim=1)[0] * 100
    res = [(class_list[idx], round(percentage[idx].item(), 3)) for idx in indices[0][:3]]
    table = tk.Label(frame, text="Top image class predictions and confidences").pack()
    for i in range(0, len(res)):
         result = tk.Label(frame, text= str(res[i][0]).upper() + ': ' + str(res[i][1]) + '%').pack()


root = tk.Tk()
root.title('Portable Image Classifier')
root.iconbitmap('class.ico')
root.resizable(False, False)

tit = tk.Label(root, text="Portable Image Classifier", padx=25, pady=6, font=("", 12)).pack()

canvas = tk.Canvas(root, height=500, width=500, bg='grey')
canvas.pack()

frame = tk.Frame(root, bg='white')
frame.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)

chose_image = tk.Button(root, text='Choose Image',
                        padx=35, pady=10,
                        fg="white", bg="grey", command=load_img)
chose_image.pack(side=tk.LEFT)


class_image = tk.Button(root, text='Classify Image',
                        padx=35, pady=10,
                        fg="white", bg="grey", command=classify)
class_image.pack(side=tk.RIGHT)


alexnet = models.alexnet(pretrained=True)
alexnet.eval()

with open('imagenet_class_index.json') as f:
    classes = json.loads(f.read())

class_list = [i[1] for i in classes.values()]

transform = transforms.Compose([
 transforms.Resize(256),
 transforms.CenterCrop(224),
 transforms.ToTensor(),
 transforms.Normalize(
 mean=[0.485, 0.456, 0.406],
 std=[0.229, 0.224, 0.225]
 )])

root.mainloop()

