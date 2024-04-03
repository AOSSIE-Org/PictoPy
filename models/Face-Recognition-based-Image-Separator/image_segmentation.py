#Neccessary Imports

import os
import cv2
import pickle
import numpy as np
import face_recognition

#Save encodings
def saveEncodings(encs,names,fname="encodings.pickle"):
    """
    Save encodings in a pickle file to be used in future.

    Parameters
    ----------
    encs : List of np arrays
        List of face encodings.
    names : List of strings
        List of names for each face encoding.
    fname : String, optional
        Name/Location for pickle file. The default is "encodings.pickle".

    Returns
    -------
    None.

    """
    
    data=[]
    d = [{"name": nm, "encoding": enc} for (nm, enc) in zip(names, encs)]
    data.extend(d)

    encodingsFile=fname
    
    # dump the facial encodings data to disk
    print("[INFO] serializing encodings...")
    f = open(encodingsFile, "wb")
    f.write(pickle.dumps(data))
    f.close()    

#Function to read encodings
def readEncodingsPickle(fname):
    """
    Read Pickle file.

    Parameters
    ----------
    fname : String
        Name of pickle file.(Full location)

    Returns
    -------
    encodings : list of np arrays
        list of all saved encodings
    names : List of Strings
        List of all saved names

    """
    
    data = pickle.loads(open(fname, "rb").read())
    data = np.array(data)
    encodings = [d["encoding"] for d in data]
    names=[d["name"] for d in data]
    return encodings,names

#Function to create encodings and get face locations
def createEncodings(image):
    """
    Create face encodings for a given image and also return face locations in the given image.

    Parameters
    ----------
    image : cv2 mat
        Image you want to detect faces from.

    Returns
    -------
    known_encodings : list of np array
        List of face encodings in a given image
    face_locations : list of tuples
        list of tuples for face locations in a given image

    """
    
    #Find face locations for all faces in an image
    face_locations = face_recognition.face_locations(image)
    
    #Create encodings for all faces in an image
    known_encodings=face_recognition.face_encodings(image,known_face_locations=face_locations)
    return known_encodings,face_locations

#Function to compare encodings
def compareFaceEncodings(unknown_encoding,known_encodings,known_names):
    """
    Compares face encodings to check if 2 faces are same or not.

    Parameters
    ----------
    unknown_encoding : np array
        Face encoding of unknown people.
    known_encodings : np array
        Face encodings of known people.
    known_names : list of strings
        Names of known people

    Returns
    -------
    acceptBool : Bool
        face matched or not
    duplicateName : String
        Name of matched face
    distance : Float
        Distance between 2 faces

    """
    duplicateName=""
    distance=0.0
    matches = face_recognition.compare_faces(known_encodings, unknown_encoding,tolerance=0.5)
    face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    best_match_index = np.argmin(face_distances)
    distance=face_distances[best_match_index]
    if matches[best_match_index]:
        acceptBool=True
        duplicateName=known_names[best_match_index]
    else:
        acceptBool=False
        duplicateName=""
    return acceptBool,duplicateName,distance

#Save Image to new directory
def saveImageToDirectory(image,name,imageName):
    """
    Saves images to directory.

    Parameters
    ----------
    image : cv2 mat
        Image you want to save.
    name : String
        Directory where you want the image to be saved.
    imageName : String
        Name of image.

    Returns
    -------
    None.

    """
    path="./output/"+name
    if os.path.exists(path):
        pass
    else:
        os.mkdir(path)
    cv2.imwrite(path+"/"+imageName,image)
    


#Function for creating encodings for known people
def processKnownPeopleImages(path="./People/",saveLocation="./known_encodings.pickle"):
    """
    Process images of known people and create face encodings to compare in future.
    Eaach image should have just 1 face in it.

    Parameters
    ----------
    path : STRING, optional
        Path for known people dataset. The default is "./People".
        It should be noted that each image in this dataset should contain only 1 face.
    saveLocation : STRING, optional
        Path for storing encodings for known people dataset. The default is "./known_encodings.pickle in current directory".

    Returns
    -------
    None.

    """
    
    known_encodings=[]
    known_names=[]
    for img in os.listdir(path):
        imgPath=path+img

        #Read image
        image=cv2.imread(imgPath)
        name=img.rsplit('.')[0]
        #Resize
        image=cv2.resize(image,(0,0),fx=0.2,fy=0.2,interpolation=cv2.INTER_LINEAR)
        
        #Get locations and encodings
        encs,locs=createEncodings(image)
        
        known_encodings.append(encs[0])
        known_names.append(name)
        
        for loc in locs:
            top, right, bottom, left=loc
            
        #Show Image
        cv2.rectangle(image,(left,top),(right,bottom),color=(255,0,0),thickness=2)
        cv2.imshow("Image",image)
        cv2.waitKey(1)
        cv2.destroyAllWindows()
    saveEncodings(known_encodings,known_names,saveLocation)

#Function for processing dataset images
def processDatasetImages(path="./Dataset/",saveLocation="./dataset_encodings.pickle"):
    """
    Process image in dataset from where you want to separate images.
    It separates the images into directories of known people, groups and any unknown people images.
    Parameters
    ----------
    path : STRING, optional
        Path for known people dataset. The default is "./People".
        It should be noted that each image in this dataset should contain only 1 face.
    saveLocation : STRING, optional
        Path for storing encodings for known people dataset. The default is "./known_encodings.pickle in current directory".

    Returns
    -------
    None.

    """
    #Read pickle file for known people to compare faces from
    people_encodings,names=readEncodingsPickle("./known_encodings.pickle")
    
    for img in os.listdir(path):
        imgPath=path+img

        #Read image
        image=cv2.imread(imgPath)
        orig=image.copy()
        
        #Resize
        image=cv2.resize(image,(0,0),fx=0.2,fy=0.2,interpolation=cv2.INTER_LINEAR)
        
        #Get locations and encodings
        encs,locs=createEncodings(image)
        
        #Save image to a group image folder if more than one face is in image
        if len(locs)>1:
            saveImageToDirectory(orig,"Group",img)
        
        
        #Processing image for each face
        i=0
        knownFlag=0
        for loc in locs:
            top, right, bottom, left=loc
            unknown_encoding=encs[i]
            i+=1
            acceptBool,duplicateName,distance=compareFaceEncodings(unknown_encoding,people_encodings,names)
            if acceptBool:
                saveImageToDirectory(orig, duplicateName, img)
                knownFlag=1
        if knownFlag==1:
            print("Match Found")
        else:
            saveImageToDirectory(orig,"Unknown",img)
        
        #Show Image
        cv2.rectangle(image,(left,top),(right,bottom),color=(255,0,0),thickness=2)
        cv2.imshow("Image",image)
        cv2.waitKey(1)
        cv2.destroyAllWindows()

        
def main():
    """
    Main Function.

    Returns
    -------
    None.

    """
    datasetPath="./Dataset/"
    peoplePath="./People/"
    processKnownPeopleImages(path=peoplePath)
    processDatasetImages(path=datasetPath)
    print("Completed")

if __name__=="__main__":
    main()