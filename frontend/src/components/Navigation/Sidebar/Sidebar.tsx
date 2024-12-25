import { Link, useLocation } from 'react-router-dom';
import {
  AlbumIcon,
  FileIcon,
  HomeIcon,
  SettingsIcon,
  VideoIcon,
} from '@/components/ui/Icons/Icons';

function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const linkClasses = (path: string) =>
    `flex items-center flex-col gap-2 ${
      isActive(path)
        ? 'text-[#6465F3] glow'
        : 'hover:text-gray-500 dark:text-gray-400 dark:hover:text-gray-50'
    }`;

  return (
    <div className="sidebar m-4 flex w-40 flex-col justify-between space-y-4 rounded-3xl border border-gray-200 dark:border-gray-800 bg-theme-light dark:bg-theme-dark p-4">
      <div className="mt-2 flex flex-col gap-10">
        <Link to="/home" className={linkClasses('/home')}>
          <HomeIcon
            className="h-5 w-5"
            fill={isActive('/home') ? '#6465F3' : 'currentColor'}
          />
          <span className="font-sans">Home</span>
        </Link>
        <Link to="/ai-tagging" className={linkClasses('/ai-tagging')}>
          <FileIcon
            className="h-5 w-5"
            fill={isActive('/ai-tagging') ? '#6465F3' : 'currentColor'}
          />
          <span className="font-sans">AI Tagging</span>
        </Link>

        <Link to="/videos" className={linkClasses('/videos')}>
          <VideoIcon
            className="h-5 w-5"
            fill={isActive('/videos') ? '#6465F3' : 'currentColor'}
          />
          <span className="font-sans">Videos</span>
        </Link>
        <Link to="/albums" className={linkClasses('/albums')}>
          <AlbumIcon
            className="h-5 w-5"
            fill={isActive('/albums') ? '#6465F3' : 'currentColor'}
          />
          <span className="font-sans">Albums</span>
        </Link>
      </div>
      <Link to="/settings" className={linkClasses('/settings')}>
        <SettingsIcon
          fill={isActive('/settings') ? '#6465F3' : 'currentColor'}
        />
        <span className="font-sans">Settings</span>
      </Link>
    </div>
  );
}

export default Sidebar;
