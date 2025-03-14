import type React from 'react';
import { useState, useEffect } from 'react';
import { convertFileSrc, invoke } from '@tauri-apps/api/core';
import { Unlock, Shield, Lock } from 'lucide-react';
import MediaView from '../Media/MediaView';
import { motion } from 'framer-motion';

interface SecureMedia {
  id: string;
  url: string;
  path: string;
}

const SecureFolder: React.FC = () => {
  const [isSetup, setIsSetup] = useState<boolean>(false);
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [secureMedia, setSecureMedia] = useState<SecureMedia[]>([]);
  const [unlocked, setUnlocked] = useState(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number | null>(
    null,
  );

  useEffect(() => {
    checkSecureFolderStatus();
  }, []);

  const checkSecureFolderStatus = async () => {
    try {
      const status = await invoke<boolean>('check_secure_folder_status');
      setIsSetup(status);
    } catch (error) {
      console.error('Failed to check secure folder status:', error);
    }
  };

  const handleSetupSecureFolder = async () => {
    if (password !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    if (password.length < 4) {
      setError('Password must be at least 4 characters long');
      return;
    }

    try {
      await invoke('create_secure_folder', { password });
      setIsSetup(true);
      setError('');
    } catch (error) {
      setError(`Failed to create secure folder: ${error}`);
    }
  };

  const handleUnlockSecureFolder = async () => {
    try {
      const unlocked = await invoke<boolean>('unlock_secure_folder', {
        password,
      });
      setUnlocked(unlocked);
      if (unlocked) {
        loadSecureMedia();
      } else {
        setError('Incorrect password');
      }
    } catch (error) {
      setError(`Failed to unlock secure folder: ${error}`);
    }
  };

  const loadSecureMedia = async () => {
    try {
      const media = await invoke<SecureMedia[]>('get_secure_media', {
        password,
      });
      const mediaWithConvertedUrls = media.map((item) => ({
        ...item,
        url: convertFileSrc(item.url.replace('file://', '')),
      }));
      setSecureMedia(mediaWithConvertedUrls);
    } catch (error) {
      console.error('Failed to load secure media:', error);
    }
  };

  const handleMediaClick = (index: number) => {
    setSelectedMediaIndex(index);
  };

  const handleCloseMediaView = () => {
    setSelectedMediaIndex(null);
    loadSecureMedia(); // Reload media in case any changes were made
  };

  const handleRemoveFromSecureFolder = async (fileName: string) => {
    try {
      await invoke('remove_from_secure_folder', { fileName, password });
      loadSecureMedia(); // Reload the secure media list
    } catch (error) {
      console.error('Failed to remove file from secure folder:', error);
    }
  };

  if (!isSetup) {
    return (
      <div className="mx-auto h-fit w-full max-w-md py-8">
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="overflow-hidden rounded-xl bg-white/80 p-6 backdrop-blur-md shadow-lg dark:bg-gray-800/90 dark:shadow-gray-900/30 border border-gray-100 dark:border-gray-700"
        >
          <div className="flex flex-col items-center mb-6">
            <Shield className="h-16 w-16 text-blue-500 dark:text-blue-400 mb-2" />
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent dark:from-blue-400 dark:to-purple-400">
              Set Up Secure Folder
            </h2>
          </div>
          <div className="space-y-4">
            <div className="relative">
              <input
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white/50 dark:bg-gray-700/50 px-4 py-3 text-gray-700 dark:text-gray-200 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 focus:outline-none transition-all duration-200"
              />
              <Lock className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
            </div>
            <div className="relative">
              <input
                type="password"
                placeholder="Confirm password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white/50 dark:bg-gray-700/50 px-4 py-3 text-gray-700 dark:text-gray-200 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 focus:outline-none transition-all duration-200"
              />
              <Lock className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleSetupSecureFolder}
              className="focus:shadow-outline w-full rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-3 font-bold text-white shadow-lg hover:from-blue-600 hover:to-purple-700 focus:outline-none transition-all duration-300 ease-in-out transform"
            >
              Create Secure Folder
            </motion.button>
            {error && <p className="text-red-500 bg-red-100 dark:bg-red-900/30 p-3 rounded-lg text-sm font-medium">{error}</p>}
          </div>
        </motion.div>
      </div>
    );
  }

  if (unlocked && secureMedia.length === 0) {
    return (
      <div className="flex w-full items-center justify-center h-96">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4 text-center"
        >
          <Shield className="h-24 w-24 text-gray-300 dark:text-gray-600" />
          <p className="text-3xl font-bold text-gray-500 dark:text-gray-400">No Images in Secure Folder</p>
          <p className="text-gray-500 max-w-md">Add images to your secure folder to view them here.</p>
        </motion.div>
      </div>
    );
  }

  if (secureMedia.length === 0) {
    return (
      <div className="mx-auto h-fit w-full max-w-md py-8">
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="overflow-hidden rounded-xl bg-white/80 p-6 backdrop-blur-md shadow-lg dark:bg-gray-800/90 dark:shadow-gray-900/30 border border-gray-100 dark:border-gray-700"
        >
          <div className="flex flex-col items-center mb-6">
            <Shield className="h-16 w-16 text-blue-500 dark:text-blue-400 mb-2" />
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent dark:from-blue-400 dark:to-purple-400">
              Unlock Secure Folder
            </h2>
          </div>
          <div className="space-y-4">
            <div className="relative">
              <input
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white/50 dark:bg-gray-700/50 px-4 py-3 text-gray-700 dark:text-gray-200 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 focus:outline-none transition-all duration-200"
              />
              <Lock className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleUnlockSecureFolder}
              className="focus:shadow-outline w-full rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-3 font-bold text-white shadow-lg hover:from-blue-600 hover:to-purple-700 focus:outline-none transition-all duration-300 ease-in-out transform"
            >
              Unlock
            </motion.button>
            {error && <p className="text-red-500 bg-red-100 dark:bg-red-900/30 p-3 rounded-lg text-sm font-medium">{error}</p>}
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8 flex items-center gap-3">
        <Shield className="h-6 w-6 text-blue-500" /> 
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          Secure Gallery
        </h2>
      </div>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
      >
        {secureMedia.map((media, index) => (
          <motion.div
            key={media.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="relative aspect-square cursor-pointer overflow-hidden rounded-xl transition-all duration-300 hover:shadow-xl group"
            onClick={() => handleMediaClick(index)}
          >
            <img
              src={media.url || '/placeholder.svg'}
              alt="Secure media"
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveFromSecureFolder(media.id);
              }}
              className="absolute right-2 top-2 rounded-full bg-white/20 backdrop-blur-md p-2 text-white shadow-lg hover:bg-white/40 transition-all duration-300 transform opacity-0 group-hover:opacity-100 scale-90 group-hover:scale-100"
              aria-label="Remove from secure folder"
            >
              <Unlock className="h-4 w-4" />
            </button>
          </motion.div>
        ))}
      </motion.div>
      {selectedMediaIndex !== null && (
        <MediaView
          initialIndex={selectedMediaIndex}
          onClose={handleCloseMediaView}
          allMedia={secureMedia}
          currentPage={1}
          itemsPerPage={secureMedia.length}
          type="image"
          isSecureFolder={true}
        />
      )}
    </div>
  );
};

export default SecureFolder;
