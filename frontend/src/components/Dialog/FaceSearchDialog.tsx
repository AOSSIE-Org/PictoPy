import { useState } from 'react';
import { Upload, Camera, ScanFace } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useDispatch } from 'react-redux';
import { useFile } from '@/hooks/selectFile';
import { startSearch, setResults, clearSearch } from '@/features/searchSlice';
import type { Image } from '@/types/Media';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchSearchedFaces } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useNavigate } from 'react-router';
import { ROUTES } from '@/constants/routes';
import WebcamComponent from '../WebCam/WebCamComponent';
export function FaceSearchDialog() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [capturedImageUrl, setCapturedImageUrl] = useState<string | null>(null);
  const { pickSingleFile } = useFile({ title: 'Select File' });
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { mutate: getSearchImages } = usePictoMutation({
    mutationFn: async (path: string) => fetchSearchedFaces({ path }),
    onSuccess: (data) => {
      const result = data?.data as Image[];
      dispatch(hideLoader());
      setIsDialogOpen(false);
      if (result && result.length > 0) {
        dispatch(setResults(result));
      } else {
        dispatch(clearSearch());
        dispatch(
          showInfoDialog({
            title: 'No Matches Found',
            message:
              'We couldn’t find any matching faces in your gallery for this photo.',
            variant: 'info',
          }),
        );
      }
    },
    onError: () => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Search Failed',
          message: 'There was an error while searching for faces.',
          variant: 'error',
        }),
      );
    },
  });
  const saveImageLocally = async (base64Image: string) => {
    try {
      // Convert base64 to blob
      const response = await fetch(base64Image);
      const blob = await response.blob();

      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Create a temporary anchor element and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `face-search-${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();

      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Also use the image for face search
      dispatch(startSearch(base64Image));
      dispatch(showLoader('Searching faces...'));
      getSearchImages(base64Image);
    } catch (error) {
      console.error('Error saving image:', error);
      dispatch(
        showInfoDialog({
          title: 'Save Failed',
          message: 'There was an error saving the captured image.',
          variant: 'error',
        }),
      );
    }
  };
  const handleWebCam = async () => {
    setShowCamera(true);
    setCapturedImageUrl(null);
  };

  const handlePickFile = async () => {
    navigate(`/${ROUTES.HOME}`);
    setIsDialogOpen(false);
    const filePath = await pickSingleFile();
    if (filePath) {
      dispatch(startSearch(filePath));
      dispatch(showLoader('Searching faces...'));
      getSearchImages(filePath);
    }
  };
  const handleSaveCapturedImage = () => {
    if (capturedImageUrl) {
      console.log(capturedImageUrl);
      saveImageLocally(capturedImageUrl);
      setShowCamera(false);
      setCapturedImageUrl(null);
      setIsDialogOpen(false);
      navigate(`/${ROUTES.HOME}`);
    }
  };

  const handleCancelWebcam = () => {
    setShowCamera(false);
    setCapturedImageUrl(null);
  };
  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button
          onClick={() => setIsDialogOpen(true)}
          variant="ghost"
          size="icon"
          className="h-8 w-8 p-1"
        >
          <ScanFace className="h-4 w-4" />
          <span className="sr-only">Face Detection Search</span>
        </Button>
      </DialogTrigger>
      <DialogContent className={showCamera ? 'sm:max-w-2xl' : 'sm:max-w-md'}>
        <DialogHeader>
          <DialogTitle>Face Detection Search</DialogTitle>
          <DialogDescription>
            {showCamera
              ? 'Capture a photo to search for matching faces'
              : 'Search for images containing specific faces by uploading a photo or using your webcam.'}
          </DialogDescription>
        </DialogHeader>

        {!showCamera ? (
          <>
            <div className="grid grid-cols-2 gap-4 py-4">
              <Button
                onClick={handlePickFile}
                disabled={false}
                className="flex h-32 flex-col items-center justify-center gap-2 p-0"
                variant="outline"
              >
                <Upload className="text-muted-foreground mb-1 h-8 w-8" />
                <span className="text-sm font-medium">Upload Photo</span>
                <span className="text-muted-foreground text-center text-xs">
                  Browse your computer
                </span>
              </Button>

              <Button
                onClick={handleWebCam}
                disabled={false}
                className="flex h-32 flex-col items-center justify-center gap-2 p-0"
                variant="outline"
              >
                <Camera className="text-muted-foreground mb-1 h-8 w-8" />
                <span className="text-sm font-medium">Use Webcam</span>
                <span className="text-muted-foreground text-center text-xs">
                  Capture with camera
                </span>
              </Button>
            </div>

            <p className="text-muted-foreground mt-2 text-xs">
              PictoPy will analyze the face and find matching images in your
              gallery.
            </p>
          </>
        ) : (
          <div className="py-4">
            <div className="relative">
              <Button
                onClick={handleCancelWebcam}
                variant="ghost"
                size="icon"
                className="absolute top-0 right-0 z-10 h-8 w-8"
              >
                X
              </Button>

              <WebcamComponent
                setShowCamera={setShowCamera}
                setImageUrl={setCapturedImageUrl}
              />

              {capturedImageUrl && (
                <div className="mt-4 flex flex-col items-center gap-4">
                  <div className="text-muted-foreground text-sm">
                    Photo captured! Click "Save & Search" to save locally and
                    search for faces.
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handleSaveCapturedImage}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Save & Search
                    </Button>
                    <Button
                      onClick={() => setCapturedImageUrl(null)}
                      variant="outline"
                    >
                      Retake
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
