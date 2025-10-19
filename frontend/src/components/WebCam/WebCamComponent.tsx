import { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { X, RotateCcw, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useDispatch } from 'react-redux';
import { startSearch, setResults, clearSearch } from '@/features/searchSlice';
import type { Image } from '@/types/Media';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchSearchedFacesBase64 } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';

const videoConstraints = {
  facingMode: 'user',
};

interface WebcamComponentProps {
  isOpen: boolean;
  onClose: () => void;
}

function WebcamComponent({ isOpen, onClose }: WebcamComponentProps) {
  const [showCamera, setShowCamera] = useState(true);
  const [capturedImageUrl, setCapturedImageUrl] = useState<string | null>(null);
  const webcamRef = useRef<Webcam>(null);
  const dispatch = useDispatch();

  const { mutate: getSearchImagesBase64 } = usePictoMutation({
    mutationFn: async (base64_data: string) =>
      fetchSearchedFacesBase64({ base64_data }),
    onSuccess: (data) => {
      const result = data?.data as Image[];
      dispatch(hideLoader());
      handleClose();
      if (result && result.length > 0) {
        dispatch(setResults(result));
      } else {
        dispatch(clearSearch());
        dispatch(
          showInfoDialog({
            title: 'No Matches Found',
            message:
              "We couldn't find any matching faces in your gallery for this photo.",
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

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCapturedImageUrl(imageSrc);
      setShowCamera(false);
    }
  }, [webcamRef]);

  const handleRetake = () => {
    setCapturedImageUrl(null);
    setShowCamera(true);
  };

  const handleSearchCapturedImage = () => {
    handleClose();
    if (capturedImageUrl) {
      dispatch(startSearch(capturedImageUrl));
      dispatch(showLoader('Searching faces...'));
      getSearchImagesBase64(capturedImageUrl);
    } else {
      dispatch(
        showInfoDialog({
          title: 'Capture Failed',
          message: 'An unexpected error occurred during capture.',
          variant: 'error',
        }),
      );
    }
  };

  const handleClose = () => {
    setShowCamera(false);
    setCapturedImageUrl(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {capturedImageUrl ? 'Captured Photo' : 'Take a Photo'}
          </DialogTitle>
          <DialogDescription>
            {capturedImageUrl
              ? 'Review your photo and search for matching faces'
              : 'Position your face in the frame and capture'}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center gap-4 py-4">
          {showCamera && !capturedImageUrl ? (
            <div className="flex flex-col items-center gap-4">
              <Webcam
                audio={false}
                height={500}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                width={500}
                videoConstraints={videoConstraints}
                className="rounded-lg border"
              />
              <Button onClick={capture} className="w-40">
                Capture Photo
              </Button>
            </div>
          ) : capturedImageUrl ? (
            <div className="flex flex-col items-center gap-4">
              <img
                src={capturedImageUrl}
                alt="Captured"
                className="max-h-96 rounded-lg border"
              />
              <div className="flex gap-3">
                <Button
                  onClick={handleRetake}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  Retake
                </Button>
                <Button
                  onClick={handleSearchCapturedImage}
                  className="flex items-center gap-2"
                >
                  <Search className="h-4 w-4" />
                  Search
                </Button>
                <Button
                  onClick={handleClose}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <X className="h-4 w-4" />
                  Close
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default WebcamComponent;
