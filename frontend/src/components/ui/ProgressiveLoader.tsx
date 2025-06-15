import type React from 'react';
import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocalStorage } from '@/hooks/LocalStorage';
import {
  queryClient,
  usePictoMutation,
  usePictoQuery,
} from '@/hooks/useQueryExtensio';
import { addFolder, getProgress } from '../../../api/api-functions/images';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface ProgressiveFolderLoaderProps {
  additionalFolders?: string[];
  setAdditionalFolders?: (folders: string[]) => void;
}

const ProgressiveFolderLoader: React.FC<ProgressiveFolderLoaderProps> = ({
  additionalFolders = [],
  setAdditionalFolders,
}) => {
  const [storedFolderPaths] = useLocalStorage<string[]>('folderPaths', []);
  const [addedFolders, setAddedFolders] = useLocalStorage<string[]>(
    'addedFolders',
    [],
  );
  const [isComplete, setIsComplete] = useState(true);
  const [autoAdd] = useLocalStorage('auto-add-folder', 'false');
  const [showError, setShowError] = useState(false);
  const isProcessingRef = useRef(false);

  const combinedFolderPaths =
    additionalFolders.length > 0 ? additionalFolders : storedFolderPaths;

  const { mutate: addFolderAPI, errorMessage } = usePictoMutation({
    mutationFn: addFolder,
    onSuccess: () => {
      const newAddedFolders = Array.from(
        new Set([...combinedFolderPaths, ...addedFolders]),
      );
      setAddedFolders(newAddedFolders);
      if (setAdditionalFolders) {
        setAdditionalFolders([]);
      }
      queryClient.invalidateQueries({ queryKey: ['all-images'] });
    },
    onError: () => {
      isProcessingRef.current = false;
      setIsComplete(true);
      queryClient.invalidateQueries({ queryKey: ['all-images'] });
      queryClient.invalidateQueries({ queryKey: ['ai-tagging-images', 'ai'] });
      setShowError(true);
      setTimeout(() => setShowError(false), 5000);
    },
    autoInvalidateTags: ['ai-tagging-images', 'ai'],
  });

  const { successData: progress } = usePictoQuery({
    queryFn: async () => await getProgress(),
    queryKey: ['ai-tagging-images', 'ai', 'progress'],
    refetchInterval: !isComplete ? 1000 : false,
    enabled: !showError && !isComplete,
  });

  const processFolder = useCallback(
    (foldersToAdd: string[]) => {
      if (!isProcessingRef.current && foldersToAdd.length > 0) {
        isProcessingRef.current = true;
        setIsComplete(false);
        addFolderAPI(foldersToAdd);
      }
    },
    [addFolderAPI],
  );

  const autoAddFolders = useCallback(() => {
    if (autoAdd === 'true' && !isProcessingRef.current) {
      const foldersToAdd = combinedFolderPaths.filter(
        (folderPath) => !addedFolders.includes(folderPath),
      );
      processFolder(foldersToAdd);
    }
  }, [autoAdd, addedFolders, combinedFolderPaths, processFolder]);

  useEffect(() => {
    if (autoAdd === 'true') {
      autoAddFolders();
    }
  }, [autoAdd, autoAddFolders]);

  useEffect(() => {
    if (typeof progress === 'number') {
      if (progress === 100) {
        setTimeout(() => {
          isProcessingRef.current = false;
          setIsComplete(true);
        }, 1000);
      } else {
        setIsComplete(false);
      }
    }
  }, [progress]);

  useEffect(() => {
    if (additionalFolders.length > 0 && !isProcessingRef.current) {
      processFolder(additionalFolders);
    }
  }, [additionalFolders, processFolder]);

  const progressPercentage = typeof progress === 'number' ? progress : 0;

  return (
    <div className="fixed top-0 right-0 left-0 z-[1000]">
      <AnimatePresence>
        {/* Progress bar */}
        {!isComplete && progressPercentage < 100 && (
          <motion.div
            className="h-1 w-full overflow-hidden bg-gray-200"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.5, delay: 0.5 } }}
          >
            <motion.div
              className="h-full bg-gradient-to-r from-sky-400 to-blue-500"
              initial={{ width: 0 }}
              animate={{
                width: `${progressPercentage}%`,
                transition: { ease: 'easeInOut' },
              }}
            />
          </motion.div>
        )}

        {/* Loading indicator */}
        {!isComplete && progressPercentage < 100 && (
          <motion.div
            className="fixed top-4 right-4 flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-sm shadow-md dark:bg-gray-800"
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
          >
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
            <span>Processing folders... {progressPercentage.toFixed(0)}%</span>
          </motion.div>
        )}

        {/* Completion indicator */}
        {isComplete && !isProcessingRef.current && (
          <motion.div
            className="fixed top-4 right-4 flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-sm shadow-md dark:bg-gray-800"
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
          >
            <CheckCircle className="h-4 w-4 text-green-500" />
          </motion.div>
        )}

        {/* Error message */}
        {showError && errorMessage && (
          <motion.div
            className="fixed top-4 left-1/2 flex max-w-md -translate-x-1/2 transform items-center gap-2 rounded-lg border-l-4 border-red-500 bg-white px-4 py-2 text-sm shadow-md dark:bg-gray-800"
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
          >
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
            <div>
              <p className="font-medium text-red-500">Error</p>
              <p className="text-gray-600 dark:text-gray-300">{errorMessage}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProgressiveFolderLoader;
