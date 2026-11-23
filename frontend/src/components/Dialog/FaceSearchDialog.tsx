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
import { useDispatch } from 'react-redux';
import { useFile } from '@/hooks/selectFile';
import { startSearch } from '@/features/searchSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useLocation, useNavigate } from 'react-router';
import { FACE_SEARCH_PATH, isFaceSearchLocation } from '@/utils/faceSearch';
import WebcamComponent from '../WebCam/WebCamComponent';

export function FaceSearchDialog() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const { pickSingleFile } = useFile({ title: 'Select File' });
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();

  const handleWebCam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach((track) => track.stop());
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
    const filePath = await pickSingleFile();
    if (filePath) {
      setIsDialogOpen(false);
      // The results page runs the search for the photo stored here.
      dispatch(startSearch(filePath));
      navigate(FACE_SEARCH_PATH, {
        replace: isFaceSearchLocation(location),
      });
    }
  };
  return (
    <>
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogTrigger asChild>
          <Button
            onClick={() => setIsDialogOpen(true)}
            variant="ghost"
            size="icon"
            className="h-8 w-8 cursor-pointer p-1"
            title="Search with Face"
          >
            <ScanFace className="h-4 w-4" />
            <span className="sr-only">Face Detection Search</span>
          </Button>
        </DialogTrigger>

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
