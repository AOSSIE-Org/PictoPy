import React, { useState } from 'react';
import { ConfirmDialog } from '@/components/Dialog/ConfirmDialog';

export interface DeleteFolderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  folderPath: string;
  subfolderCount: number;
  /** Starting state of the "Also delete subfolders" checkbox. */
  defaultDeleteSubfolders?: boolean;
  /** deleteSubfolders=false means only this folder goes; its subfolders stay. */
  onConfirm: (
    deleteSubfolders: boolean,
    dontShowAgain: boolean,
  ) => void | Promise<void>;
}

const folderName = (path: string) =>
  path.split(/[\\/]/).filter(Boolean).pop() ?? path;

/** Asks whether a folder's subfolders should go with it or stay in the library. */
export const DeleteFolderDialog: React.FC<DeleteFolderDialogProps> = ({
  open,
  onOpenChange,
  folderPath,
  subfolderCount,
  defaultDeleteSubfolders = false,
  onConfirm,
}) => {
  // Starts from the Settings default (off = keep subfolders, the safer choice).
  const [deleteSubfolders, setDeleteSubfolders] = useState(
    defaultDeleteSubfolders,
  );
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const plural = subfolderCount === 1 ? 'subfolder' : 'subfolders';

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      setDeleteSubfolders(defaultDeleteSubfolders);
      setDontShowAgain(false);
    }
    onOpenChange(next);
  };

  return (
    <ConfirmDialog
      open={open}
      onOpenChange={handleOpenChange}
      title="Delete folder"
      description={`Remove "${folderName(folderPath)}" and its photos and videos from PictoPy. Files on your computer are not touched.`}
      confirmLabel="Delete"
      onConfirm={() => onConfirm(deleteSubfolders, dontShowAgain)}
      checkboxLabel={`Also delete ${subfolderCount} ${plural}`}
      checkboxChecked={deleteSubfolders}
      onCheckboxChange={setDeleteSubfolders}
      checkboxHint={
        deleteSubfolders
          ? `The ${subfolderCount} ${plural} and all their photos and videos will be removed from PictoPy too.`
          : `The ${plural} stay in your library with their photos and videos.`
      }
      checkboxHintDestructive={deleteSubfolders}
      dontShowAgainChecked={dontShowAgain}
      onDontShowAgainChange={setDontShowAgain}
    />
  );
};

export default DeleteFolderDialog;
