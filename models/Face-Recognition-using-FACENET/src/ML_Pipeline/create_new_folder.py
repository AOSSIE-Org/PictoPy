import os
import  errno

#function to crate new folder on given a path
def create_new_folder(path):
    try:
        #making a folder
        os.mkdir(path)

    except OSError as e:
        if e.errno != errno.EEXIST:
            raise