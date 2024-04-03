import pytube
from pytube import YouTube

def download_video(video_link, path_to_store):
    try:
        #object creation using YouTube
        yt = YouTube(video_link)

    except:
        # handle the excepton due to connection error
        print("Connection error")
    stream = yt.streams.get_by_itag("22")

    #Taking highest resolution
    stream = yt.streams.get_highest_resolution()


    try:
        #downloading the video
        stream.download(path_to_store)
        print(yt.title,"is downloaded and stored in ", path_to_store)
    except:
        print("Error while downloading the video")