import { useState } from 'react';
import { Camera, ScanFace } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useDispatch } from 'react-redux';
import { useFile } from '@/hooks/selectFile';
import { startSearch, clearSearch } from '@/features/searchSlice';
import type { Image } from '@/types/Media';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchSearchedFaces } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useNavigate } from 'react-router';
import { ROUTES } from '@/constants/routes';
import WebcamComponent from '../WebCam/WebCamComponent';

import { setImages } from '@/features/imageSlice';
export function FaceSearchDialog() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
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
        dispatch(setImages(result));
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
  const handleWebCam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach((track) => track.stop());
      navigate(`/${ROUTES.HOME}`);
      setIsDialogOpen(false);
      setShowCamera(true);
    } catch (error) {
      dispatch(
        showInfoDialog({
          title: 'Webcam Not Supported',
          message:
            'Webcam is not supported or access was denied on this device.',
          variant: 'error',
        }),
      );
    }
  };
  const handlePickFile = async () => {
    try {
      navigate(`/${ROUTES.HOME}`);
      const filePath = await pickSingleFile();
      if (filePath) {
        setIsDialogOpen(false);
        dispatch(startSearch(filePath));
        dispatch(showLoader('Searching faces...'));
        getSearchImages(filePath);
      }
    } catch (error) {
      console.error('Error selecting file:', error);
      dispatch(
        showInfoDialog({
          title: 'File Selection Error',
          message: 'Failed to open file dialog. Please try again.',
          variant: 'error',
        }),
      );
    }
  };
  return (
    <>
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <TooltipProvider>
          <Tooltip>
            <DialogTrigger asChild>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => setIsDialogOpen(true)}
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 cursor-pointer p-1"
                >
                  <ScanFace className="h-4 w-4" />
                  <span className="sr-only">Face Detection Search</span>
                </Button>
              </TooltipTrigger>
            </DialogTrigger>
            <TooltipContent>
              <p>Search for similar faces in your photo library</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Face Detection Search</DialogTitle>
            <DialogDescription>
              Search for images containing specific faces by uploading a photo
              or using your webcam.
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-4 py-4">
            {/* Upload Button */}
            <Button
              onClick={handlePickFile}
              disabled={false}
              className="flex h-32 cursor-pointer flex-col items-center justify-center gap-2 p-0"
              variant="outline"
            >
              <ScanFace className="text-muted-foreground mb-1 h-8 w-8" />
              <span className="text-sm font-medium">Upload Photo</span>
              <span className="text-muted-foreground text-center text-xs">
                Select a file from your device
              </span>
            </Button>

            {/* Webcam Button */}
            <Button
              onClick={handleWebCam}
              disabled={false}
              className="flex h-32 cursor-pointer flex-col items-center justify-center gap-2 p-0"
              variant="outline"
            >
              <Camera className="text-muted-foreground mb-1 h-8 w-8" />
              <span className="text-sm font-medium">Use Webcam</span>
              <span className="text-muted-foreground text-center text-xs">
                Capture with camera
              </span>
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <WebcamComponent
        isOpen={showCamera}
        onClose={() => setShowCamera(false)}
      />
    </>
  );
}
