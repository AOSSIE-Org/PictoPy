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
  X,
  BookImage,
} from 'lucide-react';
import CustomizationPopup from './CustomizationPopup';
import ImageCompressor from './ImageCompressor';
import { defaultStyles, CustomStyles } from './styles';

const Sidebar = () => {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCustomize, setShowCustomize] = useState(false);
  const [showImageCompressor, setShowImageCompressor] = useState(false);
  const [styles, setStyles] = useState<CustomStyles>(defaultStyles);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const isActive = (path: string) => location.pathname === path;

  useEffect(() => {
    document.body.style.backgroundColor = styles.uiBackgroundColor;
  }, [styles.uiBackgroundColor]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      (event.target as HTMLElement).click();
    }
  }, []);

  const sidebarStyle = {
    background: styles.bgColor,
    color: styles.textColor,
    borderColor: styles.borderColor,
    borderRadius: `${styles.borderRadius}px`,
    backgroundSize: 'cover',
    fontFamily: styles.fontFamily,
    fontSize: `${styles.fontSize}px`,
    width: isExpanded
      ? `${styles.expandedWidth}px`
      : `${styles.sidebarWidth}px`,
    '--bg-active': styles.activeBackgroundColor,
    '--text-active': styles.activeTextColor,
    '--bg-hover': styles.hoverBackgroundColor,
  } as React.CSSProperties;

  const navItems = [
    { path: '/home', label: 'Home', Icon: Home },
    { path: '/ai-tagging', label: 'AI Tagging', Icon: Sparkles },
    { path: '/videos', label: 'Videos', Icon: Video },
    { path: '/albums', label: 'Albums', Icon: Images },
    { path: '/settings', label: 'Settings', Icon: Settings },
    { path: '/memories', label: 'Memories', Icon: BookImage },
  ];

  return (
    <>
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
      <div className="p-4">
        <nav
          className="sidebar relative z-10 flex h-[calc(90vh-2rem)] flex-col justify-between rounded-3xl border-r transition-all duration-300 ease-in-out"
          style={sidebarStyle}
          onMouseEnter={() => setIsExpanded(true)}
          onMouseLeave={() => setIsExpanded(false)}
          aria-label="Main Navigation"
        >
          <div className="mt-2 flex flex-grow flex-col items-center">
            {navItems.map(({ path, label, Icon }) => (
              <Link
                key={path}
                to={path}
                className={`group m-1 flex flex-col items-center gap-1 rounded-lg p-4 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] ${
                  isActive(path)
                    ? 'bg-[var(--bg-active)] text-[var(--text-active)] shadow-md'
                    : 'text-default hover:bg-[var(--bg-hover)]'
                }`}
                onMouseEnter={() => setHoveredItem(path)}
                onMouseLeave={() => setHoveredItem(null)}
                aria-current={isActive(path) ? 'page' : undefined}
              >
                <Icon
                  style={{
                    width: styles.iconSize,
                    height: styles.iconSize,
                    color: styles.iconColor,
                  }}
                  aria-hidden="true"
                />
                <span className="whitespace-nowrap font-medium">{label}</span>
              </Link>
            ))}
            <button
              onClick={() => setShowImageCompressor(true)}
              className="group m-1 flex w-full flex-col items-center gap-1 rounded-lg p-4 text-default transition-all duration-300 hover:scale-[1.02] hover:bg-[var(--bg-hover)] active:scale-[0.98]"
              onMouseEnter={() => setHoveredItem('compressor')}
              onMouseLeave={() => setHoveredItem(null)}
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
              />
              <span className="font-medium">Compressor</span>
            </button>
          </div>
          <div className="flex items-center justify-center p-4">
            <button
              onClick={() => setShowCustomize(true)}
              className="bg-[var(--bg-hover)] hover:bg-[var(--bg-active)] rounded-lg p-2 transition-all duration-300 focus:outline-none"
              aria-label="Customize sidebar"
              onKeyDown={handleKeyDown}
            >
              <Palette size={20} />
            </button>
          </div>
        </nav>
      </div>

      {showCustomize && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-4 dark:bg-gray-800">
            <CustomizationPopup
              styles={styles}
              setStyles={setStyles}
              onClose={() => setShowCustomize(false)}
            />
          </div>
        </div>
      )}

      {showImageCompressor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 transition-opacity duration-300">
          <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-4 dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Image Compressor</h2>
              <button
                onClick={() => setShowImageCompressor(false)}
                className="text-gray-500 transition-all duration-300 hover:rotate-90 hover:scale-110 hover:text-gray-700 active:scale-95 dark:text-gray-400 dark:hover:text-gray-200"
                aria-label="Close Image Compressor"
              >
                <X size={24} />
              </button>
            </div>
            <ImageCompressor />
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;
