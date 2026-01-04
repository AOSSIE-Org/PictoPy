import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import {
  deselectAllImages,
  setSelectionMode,
  removeFromSelection,
} from '@/store/slices/selectionSlice';
import { Button } from '../ui/button';
import { Trash2, Tag, FolderInput, Download, X } from 'lucide-react';
import { useState } from 'react';
import { BatchTagDialog } from './BatchTagDialog';
import { useToast } from '@/hooks/use-toast';
import { getBackendUrl } from '@/utils/config';

export const BatchToolbar = () => {
  const dispatch = useDispatch();
  const { toast } = useToast();
  const { selectedImageIds } = useSelector(
    (state: RootState) => state.selection
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const [showTagDialog, setShowTagDialog] = useState(false);

  const handleBatchDelete = async () => {
    const count = selectedImageIds.length;
    if (
      !window.confirm(
        `Are you sure you want to delete ${count} image${count > 1 ? 's' : ''}? This action cannot be undone.`
      )
    ) {
      return;
    }

    setIsProcessing(true);
    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(
        `${backendUrl}/images/batch-delete`,
        {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_ids: selectedImageIds }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete images');
      }

      const result = await response.json();

      toast({
        title: 'Success',
        description: `Deleted ${result.processed} image${result.processed > 1 ? 's' : ''}`,
        variant: 'default',
      });

      dispatch(removeFromSelection(selectedImageIds));
      dispatch(deselectAllImages());

      // Refresh the page to update the gallery
      window.location.reload();
    } catch (error) {
      console.error('Batch delete failed:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete images. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchTag = async (tags: string[]) => {
    setIsProcessing(true);
    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(
        `${backendUrl}/images/batch-tag`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_ids: selectedImageIds, tags }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to tag images');
      }

      const result = await response.json();

      toast({
        title: 'Success',
        description: `Tagged ${result.processed} image${result.processed > 1 ? 's' : ''}`,
        variant: 'default',
      });

      dispatch(deselectAllImages());
    } catch (error) {
      console.error('Batch tag failed:', error);
      toast({
        title: 'Error',
        description: 'Failed to tag images. Please try again.',
        variant: 'destructive',
      });
      throw error;
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchExport = async () => {
    toast({
      title: 'Coming Soon',
      description: 'Batch export feature is under development.',
      variant: 'default',
    });
  };

  const handleBatchMove = async () => {
    toast({
      title: 'Coming Soon',
      description: 'Batch move to album feature is under development.',
      variant: 'default',
    });
  };

  if (selectedImageIds.length === 0) return null;

  return (
    <>
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 animate-in slide-in-from-bottom-5">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl px-6 py-4 flex items-center gap-4 border border-gray-200 dark:border-gray-700">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {selectedImageIds.length} selected
          </span>

          <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />

          <Button
            variant="ghost"
            size="sm"
            onClick={handleBatchDelete}
            disabled={isProcessing}
            className="hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTagDialog(true)}
            disabled={isProcessing}
            className="hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-900/20"
          >
            <Tag className="h-4 w-4 mr-2" />
            Tag
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleBatchMove}
            disabled={isProcessing}
            className="hover:bg-green-50 hover:text-green-600 dark:hover:bg-green-900/20"
          >
            <FolderInput className="h-4 w-4 mr-2" />
            Move to Album
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleBatchExport}
            disabled={isProcessing}
            className="hover:bg-purple-50 hover:text-purple-600 dark:hover:bg-purple-900/20"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>

          <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              dispatch(deselectAllImages());
              dispatch(setSelectionMode(false));
            }}
            disabled={isProcessing}
            className="hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <BatchTagDialog
        isOpen={showTagDialog}
        onClose={() => setShowTagDialog(false)}
        selectedCount={selectedImageIds.length}
        onConfirm={handleBatchTag}
      />
    </>
  );
};
