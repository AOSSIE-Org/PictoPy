import { useState, useEffect } from 'react';
import { Camera, ScanFace, ExternalLink } from 'lucide-react';
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
import { startSearch, clearSearch } from '@/features/searchSlice';
import type { Image } from '@/types/Media';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { fetchSearchedFaces } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useNavigate } from 'react-router';
import { ROUTES } from '@/constants/routes';
import WebcamComponent from '../WebCam/WebCamComponent';
import { InfoDialog } from '@/components/Dialog/InfoDialog';
import { type } from '@tauri-apps/plugin-os';
import { open } from '@tauri-apps/plugin-shell';

import { setImages } from '@/features/imageSlice';

interface PlatformSettings {
  name: string;
  instructions: string;
  settingsUrl: string | null;
  troubleshootUrl?: string;
  isWebViewPermission?: boolean;
}

const TROUBLESHOOT_URL =
  'https://aossie-org.github.io/PictoPy/Camera-Permission-Troubleshooting/';

const getPlatformSettings = (os: string): PlatformSettings => {
  switch (os) {
    case 'macos':
      return {
        name: 'macOS',
        instructions: 'System Settings → Privacy & Security → Camera',
        settingsUrl:
          'x-apple.systempreferences:com.apple.preference.security?Privacy_Camera',
      };
    case 'windows':
      return {
        name: 'Windows',
        instructions:
          'This permission is stored by the app, not Windows settings.',
        settingsUrl: null,
        troubleshootUrl: TROUBLESHOOT_URL,
        isWebViewPermission: true,
      };
    case 'linux':
      return {
        name: 'Linux',
        instructions: 'Settings → Privacy → Camera',
        settingsUrl: null,
      };
    default:
      return {
        name: 'your system',
        instructions: 'Check your system privacy settings for camera access.',
        settingsUrl: null,
      };
  }
};

export function FaceSearchDialog() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [showPermissionDeniedDialog, setShowPermissionDeniedDialog] =
    useState(false);
  const [showCameraConfirmDialog, setShowCameraConfirmDialog] = useState(false);
  const [hasAcknowledgedCameraWarning, setHasAcknowledgedCameraWarning] =
    useState(() => {
      try {
        return (
          localStorage.getItem('pictopy_camera_warning_acknowledged') === 'true'
        );
      } catch {
        try {
          return (
            sessionStorage.getItem('pictopy_camera_warning_acknowledged') ===
            'true'
          );
        } catch {
          return false;
        }
      }
    });
  const [platformSettings, setPlatformSettings] = useState<PlatformSettings>({
    name: 'your system',
    instructions: 'System Settings → Privacy → Camera',
    settingsUrl: null,
  });
  const { pickSingleFile } = useFile({ title: 'Select File' });
  const navigate = useNavigate();
  const dispatch = useDispatch();

  useEffect(() => {
    try {
      const os = type();
      setPlatformSettings(getPlatformSettings(os));
    } catch {
      setPlatformSettings(getPlatformSettings(''));
    }
  }, []);

  const handleOpenSettings = async () => {
    if (!platformSettings.settingsUrl) return;
    try {
      await open(platformSettings.settingsUrl);
    } catch {
      dispatch(
        showInfoDialog({
          title: 'Unable to Open Settings',
          message: `Could not open ${platformSettings.name} settings automatically. Please navigate to: ${platformSettings.instructions}`,
          variant: 'error',
        }),
      );
    }
  };

  const handleOpenTroubleshoot = async () => {
    if (!platformSettings.troubleshootUrl) return;
    try {
      await open(platformSettings.troubleshootUrl);
    } catch {
      dispatch(
        showInfoDialog({
          title: 'Unable to Open Link',
          message: `Could not open the troubleshooting guide. Please visit: ${platformSettings.troubleshootUrl}`,
          variant: 'error',
        }),
      );
    }
  };

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

  const handleWebCamClick = () => {
    setIsDialogOpen(false);
    if (hasAcknowledgedCameraWarning) {
      triggerCameraPermission();
    } else {
      setShowCameraConfirmDialog(true);
    }
  };

  const handleWebCamConfirmed = () => {
    setShowCameraConfirmDialog(false);
    try {
      localStorage.setItem('pictopy_camera_warning_acknowledged', 'true');
    } catch {
      // If localStorage fails, continue anyway - acknowledgment is in-memory only
    }
    setHasAcknowledgedCameraWarning(true);
    triggerCameraPermission();
  };
  const triggerCameraPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach((track) => track.stop());
      navigate(`/${ROUTES.HOME}`);
      setShowCamera(true);
    } catch (error) {
      const err = error as DOMException;
      if (err.name === 'NotAllowedError') {
        // Permission explicitly denied. Shows recovery dialog
        setIsDialogOpen(false);
        setShowPermissionDeniedDialog(true);
      } else if (err.name === 'NotFoundError') {
        // No camera hardware detected
        dispatch(
          showInfoDialog({
            title: 'No Camera Found',
            message: 'No camera hardware was detected on this device.',
            variant: 'error',
          }),
        );
      } else {
        dispatch(
          showInfoDialog({
            title: 'Camera Error',
            message: 'An unexpected error occurred while accessing the camera.',
            variant: 'error',
          }),
        );
      }
    }
  };

  const handlePickFile = async () => {
    navigate(`/${ROUTES.HOME}`);
    const filePath = await pickSingleFile();
    if (filePath) {
      setIsDialogOpen(false);
      dispatch(startSearch(filePath));
      dispatch(showLoader('Searching faces...'));
      getSearchImages(filePath);
    }
  };

  // Permission denied dialog content
  const permissionDeniedMessage = platformSettings.isWebViewPermission ? (
    // Windows: WebView2-based permission
    <div className="space-y-3">
      <p>
        Camera access was denied. The app cannot re-request permission
        automatically.
      </p>
      <p>
        On <strong>{platformSettings.name}</strong>, this permission is managed
        by the app itself, not Windows Settings. Once denied, it requires
        clearing the app's local data to reset.
      </p>
      <p className="text-muted-foreground text-xs">
        See our troubleshooting guide for detailed recovery steps.
      </p>
    </div>
  ) : (
    // macOS/Linux: OS-level permission
    <div className="space-y-3">
      <p>
        Camera access was denied. The app cannot re-request permission
        automatically.
      </p>
      <p>
        To enable camera access on <strong>{platformSettings.name}</strong>, go
        to:
      </p>
      <p className="bg-muted rounded-md px-3 py-2 font-mono text-sm">
        {platformSettings.instructions}
      </p>
      <p className="text-muted-foreground text-xs">
        Find PictoPy in the list and enable camera access, then try again.
      </p>
    </div>
  );

  return (
    <>
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogTrigger asChild>
          <Button
            onClick={() => setIsDialogOpen(true)}
            variant="ghost"
            size="icon"
            className="h-8 w-8 cursor-pointer p-1"
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
              onClick={handleWebCamClick}
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

      <InfoDialog
        isOpen={showPermissionDeniedDialog}
        onClose={() => setShowPermissionDeniedDialog(false)}
        title="Camera Access Required"
        message={permissionDeniedMessage}
        variant="warning"
        primaryAction={
          platformSettings.settingsUrl
            ? {
                label: 'Open Settings',
                icon: <ExternalLink className="h-4 w-4" />,
                onClick: handleOpenSettings,
              }
            : platformSettings.troubleshootUrl
              ? {
                  label: 'Learn how to fix this',
                  icon: <ExternalLink className="h-4 w-4" />,
                  onClick: handleOpenTroubleshoot,
                }
              : undefined
        }
      />

      {/* Pre-confirmation dialog before triggering OS permission prompt */}
      <InfoDialog
        isOpen={showCameraConfirmDialog}
        onClose={() => {
          setShowCameraConfirmDialog(false);
          setIsDialogOpen(true);
        }}
        title="Camera Permission"
        message={
          <div className="space-y-3">
            <p>
              PictoPy needs camera access for face search. Your system will ask
              for permission next.
            </p>
            <p className="font-medium text-amber-600 dark:text-amber-400">
              ⚠️ Clicking "Block" could permanently restrict access and may be
              irreversible on some platforms.
            </p>
            <p className="text-muted-foreground text-sm">
              After clicking "Continue", click "Allow" to grant camera access.
            </p>
          </div>
        }
        variant="info"
        primaryAction={{
          label: 'Continue',
          onClick: handleWebCamConfirmed,
        }}
      />
    </>
  );
}
