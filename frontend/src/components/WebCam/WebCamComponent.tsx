import { useState, useRef, useCallback, useEffect } from 'react';
import { useMutationFeedback } from '../../hooks/useMutationFeedback.tsx';
import Webcam from 'react-webcam';
import { X, RotateCcw, Search, Camera, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useDispatch } from 'react-redux';
import { startSearch, clearSearch } from '@/features/searchSlice';
import type { Image } from '@/types/Media';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchSearchedFacesBase64 } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { setImages } from '@/features/imageSlice.ts';
import { DefaultError } from '@tanstack/react-query';
import { BackendRes } from '@/hooks/useQueryExtension';

interface WebcamComponentProps {
  isOpen: boolean;
  onClose: () => void;
}

function WebcamComponent({ isOpen, onClose }: WebcamComponentProps) {
  const [showCamera, setShowCamera] = useState(true);
  const [capturedImageUrl, setCapturedImageUrl] = useState<string | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const webcamRef = useRef<Webcam>(null);
  const dispatch = useDispatch();

  const searchByFaceMutation = usePictoMutation<
    BackendRes<Image[]>,
    DefaultError,
    string,
    unknown,
    Image[]
  >({
    mutationFn: async (base64_data: string) =>
      fetchSearchedFacesBase64({ base64_data }),
  });

  useMutationFeedback(searchByFaceMutation, {
    showLoading: true,
    loadingMessage: 'Searching faces...',
    errorTitle: 'Search Error',
    errorMessage: 'Failed to search images. Please try again.',
    onSuccess: () => {
      const result = searchByFaceMutation.data?.data;
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
      searchByFaceMutation.reset();
    },
  });

  // Enumerate available video devices
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    let currentStream: MediaStream | null = null;

    const getDevices = async () => {
      try {
        currentStream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });

        currentStream.getTracks().forEach((track) => track.stop());
        currentStream = null;

        const allDevices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = allDevices.filter((d) => d.kind === 'videoinput');

        if (!isMounted) return;

        setDevices(videoDevices);

        const savedDeviceId = localStorage.getItem('preferredCamera');

        if (
          savedDeviceId &&
          videoDevices.some((d) => d.deviceId === savedDeviceId)
        ) {
          setSelectedDeviceId(savedDeviceId);
        } else if (videoDevices.length > 0) {
          setSelectedDeviceId(videoDevices[0].deviceId);
        }
      } catch (error) {
        if (!isMounted) return;
        setDevices([]);
      } finally {
        if (currentStream) {
          currentStream.getTracks().forEach((track) => track.stop());
        }
      }
    };

    getDevices();

    return () => {
      isMounted = false;
    };
  }, [isOpen]);
  const handleCameraChange = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    localStorage.setItem('preferredCamera', deviceId);
  };

  const videoConstraints = {
    deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
  };

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        setCapturedImageUrl(imageSrc);
        setShowCamera(false);
      } else {
        dispatch(
          showInfoDialog({
            title: 'Capture Failed',
            message: 'Could not capture an image. Please try again.',
            variant: 'error',
          }),
        );
      }
    }
  }, [webcamRef, dispatch]);

  const handleRetake = () => {
    setCapturedImageUrl(null);
    setShowCamera(true);
  };

  const handleSearchCapturedImage = () => {
    if (capturedImageUrl) {
      dispatch(startSearch(capturedImageUrl));
      searchByFaceMutation.mutate(capturedImageUrl);
      onClose();
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
    setShowCamera(true);
    setCapturedImageUrl(null);
    onClose();
  };

  const getSelectedDeviceLabel = () => {
    const device = devices.find((d) => d.deviceId === selectedDeviceId);
    return device?.label || 'Default Camera';
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
              {devices.length === 0 ? (
                <div className="w-full max-w-md rounded-lg border p-6 text-center">
                  <p className="font-medium">No camera detected</p>
                  <p className="mt-2 text-sm text-neutral-600">
                    Make sure your device has a camera connected and permissions
                    are granted.
                  </p>
                </div>
              ) : (
                <>
                  <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    videoConstraints={videoConstraints}
                    className="w-full max-w-md rounded-lg border"
                  />
                </>
              )}

              {/* Camera Selection Dropdown */}
              <div className="flex w-full max-w-md flex-col items-center gap-4">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full justify-between"
                      disabled={devices.length === 0}
                    >
                      <div className="flex items-center gap-2">
                        <Camera className="h-4 w-4" />
                        <span className="truncate">
                          {getSelectedDeviceLabel()}
                        </span>
                      </div>
                      <ChevronDown className="h-4 w-4 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-[var(--radix-dropdown-menu-trigger-width)]">
                    {devices.length > 1 ? (
                      devices.map((device, index) => (
                        <DropdownMenuItem
                          key={device.deviceId}
                          onClick={() => handleCameraChange(device.deviceId)}
                          className="cursor-pointer"
                        >
                          {device.label || `Camera ${index + 1}`}
                        </DropdownMenuItem>
                      ))
                    ) : (
                      <DropdownMenuItem disabled>
                        No other cameras detected
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>

                <Button onClick={capture} className="">
                  Capture Photo
                </Button>
              </div>
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
