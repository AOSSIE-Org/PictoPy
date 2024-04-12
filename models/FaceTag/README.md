# FaceTag

Organizes pictures according to peoples faces in the pictures. It also writes the peoples names in the usercomment EXIF tag. It uses the amazing [face_recognition] based on dlib. 
This brings super easy face recognition to you without uploading any to facebook, google, etc. No internet connection required! Everything stays on your computer. 


After some time initial labeling faces, I organized my entire picture collection of 20k pictures over night (FaceTag is using all cpu cores). The unrecognized faces are softlinked in the folder "unkown" (this also serves as a pool to improve face recognition for a future run).


## Usage

It can be used in the console using
```
python3 facetag.py
```
or in a jupyter notebook.



### Give a picture directory
```
python3 facetag.py  --folder demo
```
and it will recursively get all jpg files.


### Label faces first
It asks for the names of all unknown people in a picture and adds them to it's name database.
![](res/demo1.jpg)
![](res/demo2.jpg)
### Exif Comment Tag
The exif user_comment tag is filled with the names from the left to the right :-) 

![](res/exif.jpg)

### Face recognition and labeling already working automatically
Already in the folloing picture face recognition works without any further input.

![](res/demo3.jpg)

and in the next picture too:

![](res/demo6.jpg)

### Folders with Softlinks  
Additionally to EXIF tags, subfolders with softlinks are created according to the names.

![](res/folders.jpg)




## Installation

The following works on linux:
```
sudo apt install jhead python3-pip cmake libboost-all-dev  python3-tk
pip3 install numpy dlib piexif face_recognition
```
