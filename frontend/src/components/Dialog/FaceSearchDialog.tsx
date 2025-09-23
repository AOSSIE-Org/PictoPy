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
export function FaceSearchDialog() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
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
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Face Detection Search</DialogTitle>
          <DialogDescription>
            Search for images containing specific faces by uploading a photo or
            using your webcam.
          </DialogDescription>
        </DialogHeader>

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
            onClick={() => {}}
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
      </DialogContent>
    </Dialog>
  );
}
