
# coding: utf-8

# In[125]:

# This program detects faces in picture, rotates the pictures automatically according to the exif tag (jhead must be installed)
# asks for the Names of the people and adds the names as in the Note field of the Exif info.
# It uses the face_recognition library to detect automatically faces. 
# It then writes the names as "Jon Doe, John Smith, ..." to the comment exif tag  (in the order from left to right)


import face_recognition
import os, sys,stat
import numpy as np
import piexif
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pickle #pickle.dump( data, open( "file.save", "wb" ) ) #data = pickle.load( open( "file.save", "rb" ) )
import subprocess 
from pathlib import Path 
import PIL.Image
import PIL.ExifTags
from multiprocessing import Pool,cpu_count
# import piexif  (does not handle the usercomment correctly)

plt.rcParams['toolbar'] = 'None'


# ## Functions

# In[126]:

def in_notebook():
    """
    Returns ``True`` if the module is running in IPython kernel,
    ``False`` if in IPython shell or other Python shell.
    """
    return 'ipykernel' in sys.modules

if in_notebook():
    print('Running in Notebook')
else:
    print('Running in Shell')

    

def exif_info(path):
    exif = {'DateTimeOriginal':''}
    try:
        img = PIL.Image.open(path)
        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in img._getexif().items()
            if k in PIL.ExifTags.TAGS
        }
    except :
        print('Error in exif info loading')
    return exif

def ExpandDirectories(flist, ending='.jpg', not_conatin=None):
    newplotfiles = []
    if isinstance(flist,str):
        flist = [flist]
    for directory in flist:
        if os.path.isdir(directory):
            for dirpath, dirnames, files in os.walk(directory, followlinks=True):
                for name in files:
                    if (ending.lower() in name.lower()) and (not_conatin==None or not_conatin not in name  ):
                        newplotfiles += [os.path.join(dirpath, name)]
#                         print('Include '+name)
        elif os.path.isfile(directory):
            newplotfiles += [directory]
    return newplotfiles




def ShowImg(pic, title='', trim=None, Timer=1):
    if isinstance(pic,str):
        data = mpimg.imread(pic)
    else:
        data = pic
    if trim!=None:
        fig = plt.imshow(data[trim[0]:trim[2],trim[3]:trim[1]])
    else:
        fig = plt.imshow(data)
    fig.axes.get_xaxis().set_visible(False)
    fig.axes.get_yaxis().set_visible(False)
    plt.suptitle(title) 
    if Timer!=None:
        plt.show(block=False)
        if not in_notebook(): plt.pause(Timer)
        plt.close()
    else:
        plt.show(block=False)
        if not in_notebook(): plt.pause(0.3)
    return data


def arr2str(arr, sep=', ', pre_counter=False, pre_counter_str=' = '):
    output = ''
    for i,item in enumerate(arr):
        if pre_counter:      output += str(i)+pre_counter_str
        output += str(item)
        if i<len(arr)-1:     output += sep
    return output
        

def ExeCmd(cmd, errormessage='Error'):
    try:
        output = subprocess.check_output(cmd, shell=True)
        if output!= "b''":
            print(output) 
        return output
    except: 
        print(errormessage)    
    
def RotateImg(pic):
    ExeCmd("jhead -autorot \'"+pic+"\'", errormessage= 'Could not rotate picture. Is jhead installed?')
    
    
def MultipleChoice(arr, pre='', post ='Please select:'):
    text = pre+arr2str(arr, sep='\n', pre_counter=True)+'\n'+post+'\n'
    return input(text)
    
# MultipleChoice(['a','b','c'])




def Path2Dir(path,   end_sep=True):
    directory = os.path.dirname(path)
    if end_sep:
        directory = directory+sep_char
    return directory


def Path2Filename(path,  RemoveEnding = False ): 
    filename = os.path.basename(path)
    if RemoveEnding:
        filename = '.'.join(filename.split('.')[:-1])
    return filename



# ## Arguments

# In[127]:

args = {
    'folder' : ['demo'],
    'database' : 'Face_encodings.save',
    'shuffle' : True,
    'softlinks' : True,
    'softlink_folder' : 'People folders',
    'ignore_readonly' : True,
    'training' : True,
    'tolerance' : 0.48 ,
}


if not in_notebook():
    import argparse

    parser = argparse.ArgumentParser(description='Detect Faces and write them in the exif tag')
    parser.add_argument('-f','--folder',nargs='*', help='Picture folders',type=str , default=args['folder'])
    parser.add_argument('--database', help='Database File, storing the face encodings',type=str , default=args['database'])
    parser.add_argument('--shuffle', type=lambda s: s.lower() in ['true', 't', 'yes', '1'], default=args['shuffle'])
 
    for k,v in vars(parser.parse_args()).items():
        args[k] = v
    


# ## Load Database

# In[128]:

if  os.path.exists(args['database']): 
    faces = pickle.load( open( args['database'], "rb" ) )
else:
    faces = {
        'encs' : [np.zeros([128])]    ,
        'names' : np.array(['0'])     ,       
    }
    
    
    


# In[129]:

def deletePerson(k):
    print(faces['names'])
    if input('Delte  '+str(faces['names'][faces['names']==k    ])+'  (y/n)') =='y':        
        mask = faces['names']!=k    
        faces['names'] = faces['names'][mask]
        faces['encs'] = faces['encs'][mask]
        
# pickle.dump( faces, open( args['database'], "wb" ) ) #data = pickle.load( open( "file.save", "rb" ) )        
# faces['names']


# ## Recognize Faces

# In[135]:

args['folder'] = [f.replace('file://','') for f in  args['folder']]
pics = np.array(ExpandDirectories(args['folder']))
if len(pics) == 0:
    raise ValueError('No pictures found.')
# pics = np.array([f.replace('file://','') for f in  pics])

print(pics)
if args['shuffle']:
    np.random.shuffle(pics)


# In[115]:

def split_list(alist, wanted_parts=1):
    if wanted_parts==0: wanted_parts =1
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]


batch_size = 10
splitted_pics = split_list(pics,wanted_parts=len(pics)//batch_size )


# In[116]:

# The function  "parallel_map"  is a modified version from qutip. The copyright of the function below is:

#    Copyright (c) 2011 and later, Paul D. Nation and Robert J. Johansson.
#    All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are
#    met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of the QuTiP: Quantum Toolbox in Python nor the names
#       of its contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#    PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###############################################################################


def parallel_map(task, values, task_args=tuple(), task_kwargs={}, **kwargs): 
    try:
        pool = Pool(processes=cpu_count())

        async_res = [pool.apply_async(task, (value,) + task_args, task_kwargs )
                     for value in values]

        while not all([ar.ready() for ar in async_res]):
            for ar in async_res:
                ar.wait(timeout=0.1)

        pool.terminate()
        pool.join()

    except KeyboardInterrupt as e:
        pool.terminate()
        pool.join()
        raise e


    return [ar.get() for ar in async_res]


# In[117]:

# def ListExifDict(filename):
#     exif_dict = piexif.load(filename)
#     print(exif_dict)
# #     for ifd in ("0th", "Exif", "GPS", "1st", "Interop"):
# #         for k,v in exif_dict[ifd].items():
# #             print(piexif.TAGS[ifd][k]["name"],v)

# ListExifDict(pics[2])        

def WriteExifComment(filename, comment):
#     exif_dict = piexif.load(filename)
#     exif_dict["Exif"][37510] = comment
#     del exif_dict["thumbnail"]
#     im = PIL.Image.open(filename)
#     im.save(filename, "jpeg", exif=piexif.dump(exif_dict))
    ExeCmd("jhead -cl \'"+comment+"\'   \'" + filename+"\'" , errormessage='Error: Could not write Tags.' )         


# WriteExifComment(pics[2], 'test text2')        
# ListExifDict(pics[2])        


# In[ ]:

def ChooseClosestMatch(matches_bool, src_enc, faces, pic, loc, show_img=True):
    red_faces = faces['names'][matches_bool]
    distances = face_recognition.face_distance(faces['encs'][matches_bool], src_enc)
    print('Multiple possible Faces found:\n'+ 
          arr2str(["{0:.2f}".format(d)+'  '+name for d,name in zip(distances,red_faces)], sep='\n'))         
    name = red_faces[np.argmin(distances)]
    if show_img:  ShowImg(pic,title=name,  trim=loc, Timer=1)
    print('Choosing the closest match: '+name)     
    return name

def AddFace(name,enc, faces):
    faces['encs'] = np.vstack([faces['encs'],enc])
    faces['names'] = np.hstack([faces['names'],name])
    return faces

        
    
def ProcessPic(pic_idx_pic_faces_array)        :    
    pic_idx, pic, faces = pic_idx_pic_faces_array[0], pic_idx_pic_faces_array[1], pic_idx_pic_faces_array[2]
    training = args['training']
#     print("------------------------------"+"{0:.2f}".format(pic_idx/len(pics)*100)+'% ,   '+str(pic_idx)+'/'+str(len(pics)))
    print('Loading: '+pic)
    names = []
    try:
        # make it writable
        if args['ignore_readonly']:
            st = os.stat(pic)
            os.chmod(pic, st.st_mode | stat.S_IWUSR)


        RotateImg(pic)
        
        if  training:   ShowImg(pic, Timer=None)

        print('Detecting faces....')
        image = face_recognition.load_image_file(pic)
        locs = face_recognition.face_locations(image)
        encs = face_recognition.face_encodings(image, known_face_locations=locs)


        # sort according to x coordinate  (left to right)
        x_coors = np.array([l[1] for l in locs])
        sort_idxs = np.argsort(x_coors)
        locs = [locs[idx] for idx in sort_idxs]
        encs = [encs[idx] for idx in sort_idxs]

        plt.close()

        # recognize each face
        if len(encs) ==0: print('No faces found.')
        for i in range(len(encs)):
            matches_bool = np.array(face_recognition.compare_faces(faces['encs'], encs[i], tolerance=args['tolerance']) )
            
            if matches_bool.any():
                names += [ChooseClosestMatch(matches_bool, encs[i],faces, pic, locs[i], show_img=training)]            
            else:
                if training:
                    ShowImg(pic, trim=locs[i], Timer=None)
                    print('Extending tolerance:')
                    matches_bool = np.array(face_recognition.compare_faces(faces['encs'], encs[i], tolerance=1) )
                    if matches_bool.any():
                        new_name = ChooseClosestMatch(matches_bool, encs[i], faces, pic, locs[i], show_img=False)
                        mc = MultipleChoice([new_name+' is correct.', 
                                             'empty for Skip', 
                                             'Skip all unknown faces from now on. The detection is good enough.', 
                                             'Write any name to add it'], 
                                          post='Please enter a number or a new name.')
                        if mc =='2':  
                            training = False
                            names += ["unknown"]
                        elif mc !='0':  
                            new_name = mc   # mc can be empty. then it will skip later
                    else:                        
                        new_name = input('Please name this face (empty if you want to skip): ')
                    plt.close()

                    if  training and new_name!='':
                        names += [new_name]
                        faces = AddFace(new_name, encs[i], faces)
                    else:
                        print('Ok. Skipping.')
                else:
#                     ShowImg(pic, trim=locs[i], Timer=1)
                    names += ["unknown"]
                    


        if len(names)>0:   # only do something if there were faces
            cleaned_names = [name for name in names if name !="unknown"]
            print('Writing names to exif tag: '+arr2str(cleaned_names))
            WriteExifComment(pic, arr2str(cleaned_names))

            # save the database if names were added
            if training:
                pickle.dump( faces, open( args['database'], "wb" ) ) #data = pickle.load( open( "file.save", "rb" ) )

        # save softlink  (even if the name is "unknown")
        if args['softlinks'] and len(pics)>1:
            for name in names:
                namefolder = os.path.join(args['folder'][0],'..', args['softlink_folder'], name)
                if not os.path.exists(namefolder):    os.makedirs(namefolder)    
                relative_from_subfolder = os.path.join('..','..',pic)
                dst = os.path.join(namefolder,
                       exif_info(pic)['DateTimeOriginal'].replace(':','-')
                       +' '
                       + Path2Filename(pic)) 
                if not os.path.exists(dst):
                    os.symlink(relative_from_subfolder, dst)
    except KeyboardInterrupt: 
        raise
    except:
        print('Error in processing image. Skipping.')    
    return  faces, names, training
    
        

        
        

# for pic_idx, pic in enumerate(pics):
#     print("------------------------------"+"{0:.2f}".format(pic_idx/len(pics)*100)+'% ,   '+str(pic_idx)+'/'+str(len(pics)))
#     faces, names, args['training'] = ProcessPic(pic_idx, pic, faces)    

for batch_idx, batch in enumerate(splitted_pics):
    print("------------------------------"+"{0:.2f}".format(batch_idx/len(splitted_pics)*100)+'% ,   '
          +str(batch_idx)+'/'+str(len(splitted_pics))+' batches a '+str(len(batch))+' pics')
    if args['training']:  # then do it nicely one after the other such that you can input names
        for pic in batch:
            faces, names, args['training'] = ProcessPic([batch_idx//len(splitted_pics), pic, faces])
    else:
        print('Now using '+str(cpu_count())+' cores.')
        parameterlist = [[batch_idx//len(splitted_pics), pic, faces]  for pic in batch]        
        resultarray = parallel_map(ProcessPic, parameterlist)    
#         print(resultarray)  discard the result array

