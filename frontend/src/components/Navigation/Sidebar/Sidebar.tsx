import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Sparkles,
  Video,
  Images,
  Settings,
  Palette,
  FileArchiveIcon as FileCompress,
  BookImage,
  Lock,
  User,
  X,
} from 'lucide-react';
import CustomizationPopup from './CustomizationPopup';
import ImageCompressor from './ImageCompressor';
import AvatarCropper from './AvatarCropper';
import { defaultStyles, type CustomStyles } from './styles';

// Define the NavItem interface for navigation items
interface NavItem {
  path: string;
  label: string;
  Icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

// Extend CSSProperties to support custom CSS variables
type CustomCSSProperties = React.CSSProperties & {
  '--bg-active'?: string;
  '--text-active'?: string;
  '--bg-hover'?: string;
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  // const [] = useState<boolean>(false);
  const [showCustomize, setShowCustomize] = useState<boolean>(false);
  const [showImageCompressor, setShowImageCompressor] =
    useState<boolean>(false);
  const [styles, setStyles] = useState<CustomStyles>(defaultStyles);
  const [avatar, setAvatar] = useState<string | null>(null);
  const [isAvatarLoading, setIsAvatarLoading] = useState<boolean>(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [showAvatarCropper, setShowAvatarCropper] = useState<boolean>(false);
  const [croppedAvatar, setCroppedAvatar] = useState<string | null>(null);

  // Check if the current path matches the given path
  const isActive = (path: string): boolean => location.pathname === path;

  // Update the body background color when the UI background color changes
  useEffect(() => {
    document.body.style.backgroundColor = styles.uiBackgroundColor;
  }, [styles.uiBackgroundColor]);

  // Handle keyboard events for accessibility
  const handleKeyDown = useCallback((event: React.KeyboardEvent): void => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      (event.target as HTMLElement).click();
    }
  }, []);

  // Handle avatar file upload
  const handleAvatarChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ): Promise<void> => {
    const file = event.target.files?.[0];
    setAvatarError(null);

    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setAvatarError('Please upload a valid image file (JPEG, PNG, GIF)');
      return;
    }

    setIsAvatarLoading(true);

    try {
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatar(reader.result as string);
        setIsAvatarLoading(false);
        setShowAvatarCropper(true);
      };
      reader.onerror = () => {
        setAvatarError('Error reading file. Please try again.');
        setIsAvatarLoading(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      setAvatarError('An unexpected error occurred. Please try again.');
      setIsAvatarLoading(false);
    }
  };

  // Handle avatar crop completion
  const handleCropComplete = (croppedImage: string): void => {
    setCroppedAvatar(croppedImage);
    setShowAvatarCropper(false);
  };

  // Define the sidebar style
  const sidebarStyle: CustomCSSProperties = {
    background: styles.bgColor,
    color: styles.textColor,
    borderColor: styles.borderColor,
    borderRadius: `${styles.borderRadius}px`,
    backgroundSize: 'cover',
    fontFamily: styles.fontFamily,
    fontSize: `${styles.fontSize}px`,
    boxShadow:
      '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '--bg-active': styles.activeBackgroundColor,
    '--text-active': styles.activeTextColor,
    '--bg-hover': styles.hoverBackgroundColor,
  };

  // Define the navigation items
  const navItems: NavItem[] = [
    { path: '/home', label: 'Home', Icon: Home },
    { path: '/ai-tagging', label: 'AI Tagging', Icon: Sparkles },
    { path: '/videos', label: 'Videos', Icon: Video },
    { path: '/albums', label: 'Albums', Icon: Images },
    { path: '/settings', label: 'Settings', Icon: Settings },
    { path: '/secure-folder', label: 'Secure Folder', Icon: Lock },
    { path: '/memories', label: 'Memories', Icon: BookImage },
  ];

  return (
    <>
      {/* Background Video */}
      {styles.backgroundVideo && (
        <div className="fixed inset-0 z-[-1] h-full w-full overflow-hidden">
          <video
            autoPlay
            loop
            muted
            playsInline
            className="absolute left-1/2 top-1/2 h-auto min-h-full w-auto min-w-full -translate-x-1/2 -translate-y-1/2 transform object-cover"
          >
            <source src={styles.backgroundVideo} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
      )}

      {/* Sidebar */}
      <div className="p-4">
        <nav
          className="sidebar rounded-3xl relative z-10 flex h-[calc(90vh-2rem)] flex-col justify-between border-r backdrop-blur-sm transition-all duration-300 ease-in-out"
          style={sidebarStyle}
          aria-label="Main Navigation"
        >
          <div className="mt-4 flex flex-col items-center">
            {/* Avatar Section */}
            <div className="group relative mb-8">
              <div
                className={`avatar-container relative cursor-pointer transition-all duration-300 ${
                  isAvatarLoading ? 'pointer-events-none opacity-50' : ''
                }`}
                onClick={() => document.getElementById('avatarUpload')?.click()}
                onKeyDown={handleKeyDown}
                tabIndex={0}
                role="button"
                aria-label="Change profile picture"
              >
                <div className="rounded-full relative h-24 w-24 overflow-hidden border-4 border-white/30 shadow-xl transition-all duration-300 hover:border-primary hover:shadow-2xl">
                  {croppedAvatar ? (
                    <img
                      src={croppedAvatar || '/placeholder.svg'}
                      alt="User Avatar"
                      className="h-full w-full transform object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                  ) : avatar ? (
                    <img
                      src={avatar || '/placeholder.svg'}
                      alt="User Avatar"
                      className="h-full w-full transform object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-gray-700 to-gray-900">
                      <User className="h-12 w-12 text-white/90" />
                    </div>
                  )}

                  <div className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                    <span className="text-center text-sm font-medium text-white drop-shadow-md">
                      Change Photo
                    </span>
                  </div>
                </div>

                {isAvatarLoading && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="rounded-full h-8 w-8 animate-spin border-b-2 border-white"></div>
                  </div>
                )}
              </div>

              {avatarError && (
                <div className="absolute bottom-0 left-1/2 w-max max-w-[200px] -translate-x-1/2 translate-y-4 transform rounded-lg bg-red-100 px-3 py-1 text-center text-sm text-red-700">
                  {avatarError}
                </div>
              )}

              <input
                type="file"
                id="avatarUpload"
                accept="image/*"
                onChange={handleAvatarChange}
                className="sr-only"
                aria-describedby="avatarError"
              />
            </div>

            {/* Navigation Items */}
            <div className="w-full space-y-1 px-2">
              {navItems.map(({ path, label, Icon }) => (
                <Link
                  key={path}
                  to={path}
                  className={`rounded-xl group flex flex-col items-center gap-1 p-4 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] ${
                    isActive(path)
                      ? 'bg-[var(--bg-active)] text-[var(--text-active)] shadow-lg'
                      : 'text-default hover:bg-[var(--bg-hover)]'
                  }`}
                  aria-current={isActive(path) ? 'page' : undefined}
                >
                  <Icon
                    style={{
                      width: styles.iconSize,
                      height: styles.iconSize,
                      color: isActive(path)
                        ? styles.activeTextColor
                        : styles.iconColor,
                    }}
                    aria-hidden="true"
                    className="transition-transform duration-300 group-hover:scale-110"
                  />
                  <span className="mt-1 whitespace-nowrap text-xs font-medium tracking-wide">
                    {label}
                  </span>
                </Link>
              ))}

              {/* Image Compressor Button */}
              <button
                onClick={() => setShowImageCompressor(true)}
                className="text-default rounded-xl group flex w-full flex-col items-center gap-1 p-4 transition-all duration-300 hover:scale-[1.02] hover:bg-[var(--bg-hover)] active:scale-[0.98]"
                aria-label="Open Image Compressor"
                onKeyDown={handleKeyDown}
              >
                <FileCompress
                  style={{
                    width: styles.iconSize,
                    height: styles.iconSize,
                    color: styles.iconColor,
                  }}
                  aria-hidden="true"
                  className="transition-transform duration-300 group-hover:scale-110"
                />
                <span className="mt-1 text-xs font-medium tracking-wide">
                  Compressor
                </span>
              </button>
            </div>
          </div>

          {/* Customize Button */}
          <div className="flex items-center justify-center p-4">
            <button
              onClick={() => setShowCustomize(true)}
              className="rounded-full bg-[var(--bg-hover)] p-3 shadow-md transition-all duration-300 hover:bg-[var(--bg-active)] hover:shadow-lg focus:outline-none"
              aria-label="Customize sidebar"
              onKeyDown={handleKeyDown}
            >
              <Palette size={20} className="text-[var(--text-active)]" />
            </button>
          </div>
        </nav>
      </div>

      {/* Customization Popup */}
      {showCustomize && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm transition-opacity duration-300">
          <div className="rounded-2xl max-h-[90vh] w-full max-w-md overflow-y-auto bg-white/90 p-4 shadow-2xl dark:bg-gray-800/90">
            <CustomizationPopup
              styles={styles}
              setStyles={setStyles}
              onClose={() => setShowCustomize(false)}
            />
          </div>
        </div>
      )}

      {/* Image Compressor Popup */}
      {showImageCompressor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 transition-opacity duration-300">
          <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-4 dark:bg-gray-800">
            <div className="mb-4 flex justify-around">
              <h2 className="text-xl font-bold">Image Compressor</h2>
              <div
                className="p-1 hover:bg-red-500"
                onClick={() => {
                  setShowImageCompressor(false);
                }}
              >
                <X width={24}></X>
              </div>
            </div>
            <ImageCompressor />
          </div>
        </div>
      )}

      {/* Avatar Cropper Popup */}
      {showAvatarCropper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm transition-opacity duration-300">
          <div className="rounded-2xl max-h-[90vh] w-full max-w-lg overflow-y-auto bg-white/90 p-6 shadow-2xl dark:bg-gray-800/90">
            <div className="mb-6">
              <h2 className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-2xl font-bold text-transparent">
                Crop Avatar
              </h2>
            </div>
            <AvatarCropper
              image={avatar as string}
              onCropComplete={handleCropComplete}
            />
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;
