import { useState, useRef, useCallback } from 'react';
import { useMutationFeedback } from '../../hooks/useMutationFeedback.tsx';
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
import { startSearch, clearSearch } from '@/features/searchSlice';
import type { Image } from '@/types/Media';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchSearchedFacesBase64 } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { setImages } from '@/features/imageSlice.ts';

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

  const getSearchImagesBase64 = usePictoMutation({
    mutationFn: async (base64_data: string) =>
      fetchSearchedFacesBase64({ base64_data }),
  });

  useMutationFeedback(getSearchImagesBase64, {
    showLoading: true,
    loadingMessage: 'Searching faces...',
    errorTitle: 'Search Error',
    errorMessage: 'Failed to search images. Please try again.',
    onSuccess: () => {
      const result = getSearchImagesBase64.data?.data as Image[];
      if (result && result.length > 0) {
        dispatch(setImages(result));
      } else {
        dispatch(
          showInfoDialog({
            title: 'No Match Found',
            message:
              'We couldn’t find any matching faces in your gallery for this photo.',
            variant: 'info',
          }),
        );
        dispatch(setImages([]));
        dispatch(clearSearch());
      }
      getSearchImagesBase64.reset();
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
    onClose();
    if (capturedImageUrl) {
      dispatch(startSearch(capturedImageUrl));
      getSearchImagesBase64.mutate(capturedImageUrl);
    } else {
      dispatch(
        showInfoDialog({
          title: 'Capture Failed',
          message: 'An unexpected error occurred during capture.',
          variant: 'error',
        }),
      );
      handleClose();
    }
  };

  const handleClose = () => {
    setShowCamera(true);
    setCapturedImageUrl(null);
    onClose();
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) handleClose();
      }}
    >
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
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                videoConstraints={videoConstraints}
                className="w-full max-w-md rounded-lg border"
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
