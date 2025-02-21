import type React from 'react';
import { useState, useEffect } from 'react';
import { convertFileSrc, invoke } from '@tauri-apps/api/core';
import { Unlock } from 'lucide-react';
import MediaView from '../Media/MediaView';

interface SecureMedia {
  id: string;
  url: string;
  path: string;
}

const validatePassword = (password: string): string | null => {
  if (password.length < 8) {
    return 'Password must be at least 8 characters long';
  }
  
  if (!/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter';
  }
  
  if (!/[0-9]/.test(password)) {
    return 'Password must contain at least one number';
  }
  
  return null;
};

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

    const validationError = validatePassword(password);
    if (validationError) {
      setError(validationError);
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
      <div className="mx-auto h-fit w-full max-w-md overflow-hidden rounded-lg bg-white p-4 shadow-md dark:bg-gray-800">
        <div className="px-6 py-4">
          <h2 className="mb-4 text-2xl font-bold text-gray-800 dark:text-white">
            Set Up Secure Folder
          </h2>
          <div className="space-y-4">
            <input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-gray-700 focus:outline-none"
            />
            <input
              type="password"
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-gray-700 focus:outline-none"
            />
            <button
              onClick={handleSetupSecureFolder}
              className="focus:shadow-outline w-full rounded-lg bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-600 focus:outline-none"
            >
              Create Secure Folder
            </button>
            {error && <p className="text-red-500">{error}</p>}
          </div>
        </div>
      </div>
    );
  }

  if (unlocked && secureMedia.length === 0) {
    return (
      <div className="flex w-full items-center justify-center">
        <p className="text-3xl font-bold">No Images in Secure Folder</p>
      </div>
    );
  }

  if (secureMedia.length === 0) {
    return (
      <div className="mx-auto h-fit w-full max-w-md overflow-hidden rounded-lg bg-white p-4 shadow-md dark:bg-gray-800">
        <div className="px-6 py-4">
          <h2 className="mb-4 text-2xl font-bold text-gray-800 dark:text-white">
            Unlock Secure Folder
          </h2>
          <div className="space-y-4">
            <input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-gray-700 focus:outline-none"
            />
            <button
              onClick={handleUnlockSecureFolder}
              className="focus:shadow-outline w-full rounded-lg bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-600 focus:outline-none"
            >
              Unlock
            </button>
            {error && <p className="text-red-500">{error}</p>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h2 className="mb-4 text-2xl font-bold text-gray-800 dark:text-white">
        Secure Gallery
      </h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {secureMedia.map((media, index) => (
          <div
            key={media.id}
            className="relative aspect-square cursor-pointer overflow-hidden rounded-lg transition-opacity hover:opacity-75"
            onClick={() => handleMediaClick(index)}
          >
            <img
              src={media.url || '/placeholder.svg'}
              alt="Secure media"
              className="h-full w-full object-cover"
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveFromSecureFolder(media.id);
              }}
              className="rounded-full absolute right-2 top-2 bg-green-500 p-1 text-white hover:bg-red-600"
            >
              <Unlock />
            </button>
          </div>
        ))}
      </div>
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
