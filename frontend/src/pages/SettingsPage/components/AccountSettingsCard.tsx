import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { setAvatar, setName } from '@/features/onboardingSlice';
import { showGlobalAlert } from '@/features/globalAlertSlice';
import { User, Pencil } from 'lucide-react';
import SettingsCard from './SettingsCard';
import { avatars } from '@/constants/avatars';
import { CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { AvatarCropDialog } from '@/components/Dialog/avatarCropDialog';
import { pickImageFile } from '@/utils/PFPutils/pickImagePFP';

const isStoredAvatarValid = (value: string) =>
  avatars.includes(value) || value.startsWith('data:image');

export interface AccountSettingsCardHandle {
  hasUnsavedChanges: boolean;
  requestLeave: (onLeave: () => void) => void;
}

const AccountSettingsCard = forwardRef<AccountSettingsCardHandle>(
  (_props, ref) => {
    const dispatch = useDispatch();
    const [name, setLocalName] = useState(
      () => localStorage.getItem('name') || '',
    );
    const [selectedAvatar, setLocalAvatar] = useState(() => {
      const stored = localStorage.getItem('avatar') || '';
      return isStoredAvatarValid(stored) ? stored : '';
    });
    const [nameError, setNameError] = useState(false);
    const [longWordError, setLongWordError] = useState(false);
    const [isEditingName, setIsEditingName] = useState(false);
    const [nameDraft, setNameDraft] = useState(name);
    const [savedName, setSavedName] = useState(
      () => localStorage.getItem('name') || '',
    );
    const [savedAvatar, setSavedAvatar] = useState(() => {
      const stored = localStorage.getItem('avatar') || '';
      return isStoredAvatarValid(stored) ? stored : '';
    });
    const [rawImage, setRawImage] = useState<string | null>(null);
    const [cropDialogOpen, setCropDialogOpen] = useState(false);
    const [leaveDialogOpen, setLeaveDialogOpen] = useState(false);
    const [pendingLeave, setPendingLeave] = useState<(() => void) | null>(null);

    const hasUnsavedChanges =
      name !== savedName ||
      selectedAvatar !== savedAvatar ||
      (isEditingName && nameDraft !== name);

    const handleAvatarSelect = (avatar: string) => {
      setLocalAvatar(avatar);
    };

    const handleUploadClick = async () => {
      try {
        const dataUrl = await pickImageFile();
        if (!dataUrl) return;
        setRawImage(dataUrl);
        setCropDialogOpen(true);
      } catch (error) {
        console.error('Failed to read selected image:', error);
        dispatch(
          showGlobalAlert({
            title: 'Upload failed',
            message: 'Could not read the selected image. Please try again.',
          }),
        );
      }
    };

    const handleCropped = (dataUrl: string) => {
      setLocalAvatar(dataUrl);
      setRawImage(null);
    };

    const handleNameDraftChange = (value: string) => {
      const words = value.split(' ');
      const hasLongWord = words.some((word) => word.length > 30);
      if (hasLongWord) {
        setLongWordError(true);
        return;
      }
      setLongWordError(false);
      setNameDraft(value);
      if (nameError) setNameError(false);
    };

    const handleStartEditName = () => {
      setNameDraft(name);
      setIsEditingName(true);
    };

    const handleSaveNameEdit = () => {
      if (longWordError) return;
      setLocalName(nameDraft);
      setIsEditingName(false);
    };

    const handleCancelNameEdit = () => {
      setNameDraft(name);
      setLongWordError(false);
      setIsEditingName(false);
    };

    const handleSave = (): boolean => {
      if (!name.trim()) {
        setNameError(true);
        setNameDraft(name);
        setIsEditingName(true);
        return false;
      }

      setNameError(false);
      if (!selectedAvatar) return false;

      try {
        dispatch(setName(name));
        dispatch(setAvatar(selectedAvatar));
        localStorage.setItem('name', name);
        localStorage.setItem('avatar', selectedAvatar);
        setSavedName(name);
        setSavedAvatar(selectedAvatar);
        return true;
      } catch (error) {
        console.error('Failed to save settings:', error);
        dispatch(
          showGlobalAlert({
            title: 'Save failed',
            message: 'Could not save your profile changes. Please try again.',
          }),
        );
        return false;
      }
    };

    const handleDiscardChanges = () => {
      setLocalName(savedName);
      setLocalAvatar(savedAvatar);
      setNameDraft(savedName);
      setNameError(false);
      setLongWordError(false);
      setIsEditingName(false);
    };

    useEffect(() => {
      const handleBeforeUnload = (e: BeforeUnloadEvent) => {
        if (!hasUnsavedChanges) return;
        e.preventDefault();
        e.returnValue = '';
      };
      window.addEventListener('beforeunload', handleBeforeUnload);
      return () =>
        window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [hasUnsavedChanges]);

    useImperativeHandle(
      ref,
      () => ({
        hasUnsavedChanges,
        requestLeave: (onLeave: () => void) => {
          if (!hasUnsavedChanges) {
            onLeave();
            return;
          }
          setPendingLeave(() => onLeave);
          setLeaveDialogOpen(true);
        },
      }),
      [hasUnsavedChanges],
    );

    const handleLeaveSave = () => {
      const success = handleSave();
      if (!success) return;
      setLeaveDialogOpen(false);
      pendingLeave?.();
      setPendingLeave(null);
    };

    const handleLeaveDiscard = () => {
      handleDiscardChanges();
      setLeaveDialogOpen(false);
      pendingLeave?.();
      setPendingLeave(null);
    };

    const handleLeaveCancel = () => {
      setLeaveDialogOpen(false);
      setPendingLeave(null);
    };

    return (
      <SettingsCard
        icon={User}
        title="Account Information"
        description="Manage your account details and profile information."
      >
        <CardContent className="flex flex-1 flex-col items-center space-y-6 overflow-y-hidden p-2 text-center">
          <button
            type="button"
            onClick={handleUploadClick}
            aria-label="Change profile avatar"
            className="group relative inline-flex h-28 w-28 items-center justify-center rounded-full"
          >
            {selectedAvatar ? (
              <img
                src={selectedAvatar}
                alt="Current avatar"
                className="h-28 w-28 rounded-full object-cover"
              />
            ) : (
              <div className="bg-muted text-muted-foreground flex h-28 w-28 items-center justify-center rounded-full">
                <User className="h-9 w-9" />
              </div>
            )}
            <span className="border-background absolute right-0 bottom-0 flex h-8 w-8 items-center justify-center rounded-full border-2 bg-blue-500 text-white transition-transform group-hover:scale-105">
              <Pencil className="h-4 w-4" />
            </span>
          </button>

          <div className="flex flex-col items-center gap-2">
            {isEditingName ? (
              <>
                <Input
                  aria-label="Name"
                  autoFocus
                  placeholder={
                    nameError ? "Name can't be empty" : 'Enter your name'
                  }
                  value={nameDraft}
                  onChange={(e) => handleNameDraftChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleSaveNameEdit();
                    } else if (e.key === 'Escape') {
                      e.preventDefault();
                      handleCancelNameEdit();
                    }
                  }}
                  className={`h-10 w-56 text-center text-sm placeholder:text-sm ${
                    nameError
                      ? 'border-red-500 placeholder:text-red-500/80 focus-visible:ring-red-500'
                      : ''
                  }`}
                />
                {longWordError && (
                  <p className="text-xs text-red-500">
                    A single word in your name cannot exceed 30 characters.
                  </p>
                )}
                <p className="text-muted-foreground text-xs">
                  Press Enter to save • Esc to cancel
                </p>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <span className="w-4" aria-hidden="true" />
                <span className="text-lg font-medium">
                  {name || 'Add your name'}
                </span>
                <button
                  type="button"
                  onClick={handleStartEditName}
                  aria-label="Edit name"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Pencil className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>

          <div className="w-full px-[20%]">
            <Label className="mb-3 block text-base font-medium">Avatar</Label>
            <div className="grid grid-cols-4 place-items-center gap-4">
              {avatars.map((avatar) => {
                const isSelected = selectedAvatar === avatar;
                return (
                  <button
                    type="button"
                    key={avatar}
                    onClick={() => handleAvatarSelect(avatar)}
                    className={`bg-background relative inline-flex h-16 w-16 items-center justify-center rounded-full transition-all duration-300 ${
                      isSelected
                        ? 'ring-offset-background scale-90 ring-2 ring-blue-500 ring-offset-4'
                        : 'hover:ring-4 hover:ring-blue-500 hover:ring-offset-4'
                    }`}
                  >
                    <img
                      src={avatar}
                      alt="Avatar"
                      className={`h-16 w-16 rounded-full object-cover transition-all duration-300 ${
                        isSelected ? 'brightness-110' : ''
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          <Button
            className="mt-4 w-auto bg-blue-500 px-6 py-2 text-sm font-medium text-white hover:bg-blue-600"
            onClick={handleSave}
            disabled={!selectedAvatar || longWordError}
          >
            Save Changes
          </Button>
        </CardContent>

        <AvatarCropDialog
          open={cropDialogOpen}
          onOpenChange={setCropDialogOpen}
          imageSrc={rawImage}
          onCropped={handleCropped}
        />

        <Dialog open={leaveDialogOpen} onOpenChange={setLeaveDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Unsaved changes</DialogTitle>
            </DialogHeader>
            <p className="text-muted-foreground text-sm">
              You have unsaved changes to your profile. Save before leaving?
            </p>
            <DialogFooter className="flex-col gap-2 sm:flex-row">
              <Button
                type="button"
                variant="outline"
                onClick={handleLeaveCancel}
                className="sm:mr-auto"
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleLeaveDiscard}
              >
                Discard
              </Button>
              <Button type="button" onClick={handleLeaveSave}>
                Save
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </SettingsCard>
    );
  },
);

AccountSettingsCard.displayName = 'AccountSettingsCard';

export default AccountSettingsCard;
