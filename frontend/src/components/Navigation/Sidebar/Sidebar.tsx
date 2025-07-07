import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router';
import {
  Home,
  Sparkles,
  Video,
  Images,
  Settings,
  BookImage,
  Lock,
} from 'lucide-react';
import { defaultStyles, type CustomStyles } from './styles';
import { ROUTES } from '@/constants/routes';

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
  const [styles] = useState<CustomStyles>(defaultStyles);

  // Check if the current path matches the given path
  const isActive = (path: string): boolean => location.pathname === path;

  // Update the body background color when the UI background color changes
  useEffect(() => {
    document.body.style.backgroundColor = styles.uiBackgroundColor;
  }, [styles.uiBackgroundColor]);

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
    width: '100%', // Ensure full width within container
    height: '100%', // Ensure full height
  };

  // Define the navigation items
  const navItems: NavItem[] = [
    { path: `/${ROUTES.LAYOUT.HOME}`, label: 'Home', Icon: Home },
    { path: `/${ROUTES.LAYOUT.AI}`, label: 'AI Tagging', Icon: Sparkles },
    { path: `/${ROUTES.LAYOUT.VIDEOS}`, label: 'Videos', Icon: Video },
    { path: `/${ROUTES.LAYOUT.ALBUMS}`, label: 'Albums', Icon: Images },
    { path: `/${ROUTES.LAYOUT.SETTINGS}`, label: 'Settings', Icon: Settings },
    {
      path: `/${ROUTES.LAYOUT.SECURE_FOLDER}`,
      label: 'Secure Folder',
      Icon: Lock,
    },
    { path: `/${ROUTES.LAYOUT.MEMORIES}`, label: 'Memories', Icon: BookImage },
  ];

  return (
    <>
      {/* Sidebar */}
      <div className="h-fit p-4">
        <nav
          className="sidebar relative z-10 flex h-[calc(100vh-2rem)] flex-col justify-between overflow-hidden rounded-3xl border-r backdrop-blur-sm transition-all duration-300 ease-in-out"
          style={sidebarStyle}
          aria-label="Main Navigation"
        >
          <div className="scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent mt-4 flex flex-col items-center overflow-y-auto">
            {/* Navigation Items */}
            <div className="w-full space-y-1 px-3">
              {navItems.map(({ path, label, Icon }) => (
                <Link
                  key={path}
                  to={path}
                  className={`group flex flex-col items-center gap-1 rounded-xl px-2 py-3 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] ${
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
                  <span className="mt-1 text-xs font-medium tracking-wide whitespace-nowrap">
                    {label}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </nav>
      </div>
    </>
  );
};

export default Sidebar;
