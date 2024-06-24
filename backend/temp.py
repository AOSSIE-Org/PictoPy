import os

path = "/home/bassam/Documents/os/PictoPy/images"
lst = [path + "/" + x for x in os.listdir(path)]
for x in lst: print(x)