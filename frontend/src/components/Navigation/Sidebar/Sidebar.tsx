import { Link, useLocation } from 'react-router-dom';
import { Home, Sparkles, Video, Images, Settings } from 'lucide-react';

function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const linkClasses = (path: string) => {
    const baseClasses =
      'group flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-200';

    const activeClasses = `bg-white/95 dark:bg-white/10
      text-gray-900 dark:text-gray-100
      shadow-md dark:shadow-gray-900/30
      backdrop-blur-md backdrop-saturate-150
      border border-gray-200 dark:border-gray-700`;

    const inactiveClasses = `bg-transparent hover:bg-gray-50 dark:hover:bg-white/10
      text-gray-700 dark:text-gray-400
      hover:text-gray-900 dark:hover:text-gray-100
      border border-transparent
      hover:border-gray-200 dark:hover:border-gray-700
      hover:shadow-sm dark:hover:shadow-gray-900/20`;

    return `${baseClasses} ${isActive(path) ? activeClasses : inactiveClasses}`;
  };

  const iconClasses =
    'h-5 w-5 transition-transform duration-200 ease-out group-hover:scale-110';

  return (
    <div className="sidebar h-[90vh] sm:h-[90%] text-theme-dark dark:text-theme-light bg-theme-light m-2 sm:m-4 flex flex-col justify-between rounded-lg sm:rounded-2xl border border-gray-300 p-2 sm:p-4 backdrop-blur-md backdrop-saturate-150 dark:border-white/10 dark:bg-white/5 w-full sm:w-36 overflow-y-auto scrollbar-hide">
      <div className="mt-2 flex flex-col gap-4">
        <Link to="/home" className={linkClasses('/home')}>
          <Home
            className={iconClasses}
            strokeWidth={isActive('/home') ? 2.5 : 2}
          />
          <span className="text-xs sm:text-sm font-medium">Home</span>
        </Link>

        <Link to="/ai-tagging" className={linkClasses('/ai-tagging')}>
          <Sparkles
            className={iconClasses}
            strokeWidth={isActive('/ai-tagging') ? 2.5 : 2}
          />
          <span className="text-xs sm:text-sm font-medium">AI Tagging</span>
        </Link>

        <Link to="/videos" className={linkClasses('/videos')}>
          <Video
            className={iconClasses}
            strokeWidth={isActive('/videos') ? 2.5 : 2}
          />
          <span className="text-xs sm:text-sm font-medium">Videos</span>
        </Link>

        <Link to="/albums" className={linkClasses('/albums')}>
          <Images
            className={iconClasses}
            strokeWidth={isActive('/albums') ? 2.5 : 2}
          />
          <span className="text-xs sm:text-sm font-medium">Albums</span>
        </Link>
      </div>

      <Link to="/settings" className={linkClasses('/settings')}>
        <Settings
          className={`${iconClasses} transform transition-transform group-hover:rotate-90`}
          strokeWidth={isActive('/settings') ? 2.5 : 2}
        />
        <span className="text-xs sm:text-sm font-medium">Settings</span>
      </Link>
    </div>
  );
}

export default Sidebar;
