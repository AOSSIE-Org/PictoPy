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

    // Full-width card; `*:pb-0` drops the Card's bottom padding so the footer sits flush.
    return (
      <div className="@container -mt-7 w-full min-w-0 *:mx-0 *:mt-0 *:w-full *:max-w-none *:pb-0">
        <SettingsCard
          icon={User}
          title="Account Information"
          description="Manage your account details and profile information."
        >
          <CardContent
            className={cn(
              // -mt-6 cancels the gap SettingsCard adds below its divider.
              '-mt-6 p-0',
              // --k scales every size below and steps up with the card's own width.
              '[--k:1] @max-xl:[--k:0.85] @7xl:[--k:1.1] @min-[100rem]:[--k:1.2] @min-[125rem]:[--k:1.4] @min-[160rem]:[--k:1.6] @min-[200rem]:[--k:1.8]',
              // Avatar size grows with the card width up to a cap.
              '[--av:clamp(4.25rem,8cqw,calc(7rem*var(--k)))] [--gap:calc(2.25rem*var(--k))]',
              '[--fs-label:calc(0.8rem*var(--k))] [--fs-md:calc(1rem*var(--k))] [--fs-sm:calc(0.95rem*var(--k))]',
              '[--ctl-h:calc(2.75rem*var(--k))] [--field-h:calc(2.25rem*var(--k))] [--field-w:calc(20rem*var(--k))]',
            )}
          >
            <div className="flex flex-col gap-(--gap) px-8 py-(--gap) @max-xl:px-6">
              {/* TOP ROW: avatar preview + display name */}
              <div className="flex min-w-0 items-center gap-6 @max-[26rem]:flex-col @max-[26rem]:items-start">
                <Button
                  variant="ghost"
                  type="button"
                  onClick={handleUploadClick}
                  aria-label="Change profile avatar"
                  className="group focus-visible:ring-ring focus-visible:ring-offset-card relative inline-flex size-(--av) shrink-0 items-center justify-center rounded-full p-0 hover:bg-transparent focus-visible:ring-2 focus-visible:ring-offset-2"
                >
                  <span className="ring-primary/60 ring-offset-card relative inline-flex size-(--av) items-center justify-center rounded-full ring-2 ring-offset-2">
                    {selectedAvatar ? (
                      <img
                        src={selectedAvatar}
                        alt="Current avatar"
                        className="size-(--av) rounded-full object-cover"
                      />
                    ) : (
                      <div className="bg-muted text-muted-foreground flex size-(--av) items-center justify-center rounded-full">
                        <User className="size-6" />
                      </div>
                    )}
                  </span>
                  <span className="bg-primary text-primary-foreground ring-card absolute -right-0.5 -bottom-0.5 flex size-7 items-center justify-center rounded-full shadow-md ring-2">
                    <Pencil className="h-3.5 w-3.5" />
                  </span>
                </Button>

                <div className="w-full max-w-(--field-w) min-w-0 space-y-3">
                  <Label className="text-foreground/70 text-(length:--fs-label) leading-none font-semibold tracking-wider uppercase">
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
                          'bg-background focus-visible:ring-primary/30 h-(--field-h) w-full rounded-lg border px-4 text-(length:--fs-md) shadow-none focus-visible:ring-2 md:text-(length:--fs-md)',
                          nameError
                            ? 'border-destructive placeholder:text-destructive/70'
                            : 'border-border focus-visible:border-primary',
                        )}
                      />
                      {longWordError ? (
                        <p className="text-destructive text-(length:--fs-sm)">
                          A single word in your name cannot exceed 30
                          characters.
                        </p>
                      ) : (
                        <p className="text-muted-foreground text-(length:--fs-sm)">
                          Press Enter to save • Esc to cancel
                        </p>
                      )}
                    </>
                  ) : (
                    <Button
                      variant="ghost"
                      type="button"
                      onClick={handleStartEditName}
                      aria-label="Edit name"
                      className="group border-input hover:border-primary/50 bg-background hover:bg-background focus-visible:ring-primary/30 flex h-auto min-h-(--field-h) w-full min-w-0 items-center justify-between gap-3 rounded-lg border px-4 py-1.5 text-left transition-colors motion-reduce:transition-none"
                    >
                      <span className="min-w-0 text-(length:--fs-md) font-medium wrap-anywhere whitespace-normal">
                        {name || 'Add your name'}
                      </span>
                      <Pencil className="text-muted-foreground group-hover:text-foreground size-4 shrink-0 transition-colors motion-reduce:transition-none" />
                    </Button>
                  )}
                  {!isEditingName && (
                    <p className="text-muted-foreground text-(length:--fs-sm)">
                      Shown on albums and shared memories.
                    </p>
                  )}
                </div>
              </div>

              {/* AVATAR PICKER */}
              <div>
                <Label className="text-foreground/70 text-(length:--fs-label) leading-none font-semibold tracking-wider uppercase">
                  Choose avatar
                </Label>
                <div className="-m-2 overflow-x-auto p-2">
                  <div className="mt-5 grid w-max grid-cols-[repeat(8,var(--av))] gap-[calc(1.1rem*var(--k))] @max-3xl:grid-cols-[repeat(4,var(--av))]">
                    {avatars.map((avatar) => {
                      const isSelected = selectedAvatar === avatar;
                      return (
                        <Button
                          variant="ghost"
                          type="button"
                          key={avatar}
                          onClick={() => handleAvatarSelect(avatar)}
                          className={cn(
                            'group focus-visible:ring-ring focus-visible:ring-offset-card relative size-(--av) shrink-0 rounded-full p-0 transition-transform duration-200 hover:bg-transparent focus-visible:ring-2 focus-visible:ring-offset-2 motion-reduce:transition-none',
                            isSelected
                              ? 'ring-primary ring-offset-card ring-2 ring-offset-2'
                              : 'bg-muted ring-border hover:ring-foreground/30 opacity-90 ring-1 hover:opacity-100 motion-safe:hover:-translate-y-0.5',
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
                        </Button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            <div className="border-border bg-muted/30 flex flex-col items-stretch gap-4 border-t px-6 py-[calc(1rem*var(--k))] @xl:flex-row @xl:items-center @xl:justify-between @xl:px-8">
              <p
                role="status"
                aria-live="polite"
                className={cn(
                  'flex items-center gap-3 text-(length:--fs-md) font-medium',
                  hasUnsavedChanges
                    ? 'text-amber-700 dark:text-amber-500'
                    : 'text-muted-foreground',
                )}
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    'size-3 shrink-0 rounded-full transition-colors',
                    hasUnsavedChanges
                      ? 'bg-amber-500 motion-safe:animate-pulse'
                      : 'bg-green-500',
                  )}
                />
                {hasUnsavedChanges
                  ? 'You have unsaved changes'
                  : 'All changes saved'}
              </p>
              <div className="flex w-full gap-2 @max-[26rem]:flex-col-reverse @xl:w-auto @xl:justify-end">
                <Button
                  variant="outline"
                  onClick={handleDiscardChanges}
                  disabled={!hasUnsavedChanges}
                  className="h-(--ctl-h) flex-1 px-[calc(1.5rem*var(--k))] text-(length:--fs-md) font-medium @xl:flex-none"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={
                    !selectedAvatar || longWordError || !hasUnsavedChanges
                  }
                  className="h-(--ctl-h) flex-1 px-[calc(1.5rem*var(--k))] text-(length:--fs-md) font-medium @xl:flex-none"
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
      </div>
    );
  },
);

AccountSettingsCard.displayName = 'AccountSettingsCard';

export default AccountSettingsCard;
