import sys
import sklearn
import tensorflow as tf
from tensorflow import keras
import numpy as np
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rc('axes', labelsize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

# this was for the purpose of colab
# this lets me input however many images I want, 
# and they will all be output later
from google.colab import files
fileImg = files.upload()


# this is needed to output the images you select in color.
# the interpolation displays the images without trying to mess with resolution and sizes
# the axis off just means dont display the lengths and widths of the images lol
def plot_color_image(image):
    plt.imshow(image, interpolation="nearest")
    plt.axis("off")

# uses imagenet for image recognition. This and "ResNet50" could be swapped out with other 
# CNN methods for different prediction results
model = keras.applications.resnet50.ResNet50(weights="imagenet")

# everything is inside of this for loop so the last image chosen by the user
# isn't the only one displayed.
for pics in fileImg:
  img = image.load_img(pics, target_size =(224, 224))
  x = image.img_to_array(img)
  x = np.expand_dims(x, axis = 0)
  x = preprocess_input(x)

  preds = model.predict(x)

  inputs = keras.applications.resnet50.preprocess_input(x)
  Y_proba = model.predict(inputs)
  top_K = keras.applications.resnet50.decode_predictions(Y_proba, top=3)

  plot_color_image(img)
  plt.show()

# shows the results of the predictions the machine made
  for class_id, name, Y_proba in top_K[0]:
    print("  {} - {:12s} {:.2f}%".format(class_id, name, Y_proba * 100))

print()