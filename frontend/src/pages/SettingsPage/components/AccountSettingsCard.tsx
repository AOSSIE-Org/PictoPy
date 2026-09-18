import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { setAvatar, setName } from '@/features/onboardingSlice';
import { showGlobalAlert } from '@/features/globalAlertSlice';
import { User, Pencil, Check } from 'lucide-react';
import SettingsCard from './SettingsCard';
import { avatars } from '@/constants/avatars';
import { CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
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
        <CardContent className="p-0">
          <div className="grid gap-8 p-6 md:grid-cols-[minmax(0,280px)_1fr] md:gap-10 md:p-8">
            {/* LEFT: identity */}
            <div className="flex flex-col items-center md:items-start">
              <button
                type="button"
                onClick={handleUploadClick}
                aria-label="Change profile avatar"
                className="group relative inline-flex h-40 w-40 items-center justify-center rounded-full"
              >
                <span
                  aria-hidden="true"
                  className="bg-foreground/10 absolute inset-0 rounded-full opacity-0 blur-xl transition-opacity duration-300 group-hover:opacity-100"
                />
                <span className="ring-border ring-offset-card relative inline-flex h-40 w-40 items-center justify-center rounded-full ring-2 ring-offset-4">
                  {selectedAvatar ? (
                    <img
                      src={selectedAvatar}
                      alt="Current avatar"
                      className="h-40 w-40 rounded-full object-cover"
                    />
                  ) : (
                    <div className="bg-muted text-muted-foreground flex h-40 w-40 items-center justify-center rounded-full">
                      <User className="h-12 w-12" />
                    </div>
                  )}
                </span>
                <span className="bg-primary text-primary-foreground ring-card absolute right-2 bottom-2 flex h-9 w-9 items-center justify-center rounded-full shadow-lg ring-2 transition-transform group-hover:scale-105">
                  <Pencil className="h-4 w-4" />
                </span>
              </button>

              <div className="mt-8 w-full space-y-2">
                <Label className="text-muted-foreground text-xs font-semibold tracking-[0.15em] uppercase">
                  Display name
                </Label>
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
                      onBlur={handleSaveNameEdit}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleSaveNameEdit();
                        } else if (e.key === 'Escape') {
                          e.preventDefault();
                          handleCancelNameEdit();
                        }
                      }}
                      className={cn(
                        'h-10 w-full rounded-none border-0 border-b bg-transparent px-0 text-lg shadow-none focus-visible:ring-0',
                        nameError
                          ? 'border-destructive placeholder:text-destructive/70'
                          : 'border-border focus-visible:border-primary',
                      )}
                    />
                    {longWordError ? (
                      <p className="text-destructive text-xs">
                        A single word in your name cannot exceed 30 characters.
                      </p>
                    ) : (
                      <p className="text-muted-foreground text-xs">
                        Press Enter to save • Esc to cancel
                      </p>
                    )}
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={handleStartEditName}
                    aria-label="Edit name"
                    className="group border-border hover:border-foreground/40 flex w-full items-center justify-between border-b pb-2 text-left transition-colors"
                  >
                    <span className="text-lg font-medium">
                      {name || 'Add your name'}
                    </span>
                    <Pencil className="text-muted-foreground group-hover:text-foreground h-4 w-4 transition-colors" />
                  </button>
                )}
              </div>
            </div>

            {/* RIGHT: avatar picker */}
            <div>
              <Label className="text-muted-foreground text-xs font-semibold tracking-[0.15em] uppercase">
                Choose avatar
              </Label>
              <div className="mt-8 grid grid-cols-[repeat(4,5.625rem)] gap-4">
                {avatars.map((avatar) => {
                  const isSelected = selectedAvatar === avatar;
                  return (
                    <button
                      type="button"
                      key={avatar}
                      onClick={() => handleAvatarSelect(avatar)}
                      className={cn(
                        'group relative aspect-square w-full rounded-full transition-all duration-200',
                        isSelected
                          ? 'ring-primary ring-offset-card ring-2 ring-offset-2'
                          : 'ring-border hover:ring-foreground/30 ring-1 hover:-translate-y-0.5',
                      )}
                    >
                      <span className="block h-full w-full overflow-hidden rounded-full">
                        <img
                          src={avatar}
                          alt="Avatar"
                          className="h-full w-full object-cover"
                        />
                      </span>
                      {isSelected && (
                        <span className="bg-primary text-primary-foreground ring-card absolute -top-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full shadow-md ring-2">
                          <Check className="h-3.5 w-3.5" strokeWidth={3} />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* FOOTER */}
          <div className="border-border flex flex-col-reverse items-stretch gap-3 border-t px-6 py-4 sm:flex-row sm:items-center sm:justify-between md:px-8">
            <p className="text-muted-foreground text-xs">
              {hasUnsavedChanges
                ? 'You have unsaved changes'
                : 'All changes saved'}
            </p>
            <div className="flex gap-2 sm:justify-end">
              <Button
                variant="outline"
                onClick={handleDiscardChanges}
                disabled={!hasUnsavedChanges}
                className="flex-1 sm:flex-none"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={
                  !selectedAvatar || longWordError || !hasUnsavedChanges
                }
                className="flex-1 sm:flex-none"
              >
                Save Changes
              </Button>
            </div>
          </div>
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
