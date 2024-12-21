import { Link, useLocation } from 'react-router-dom';
import { Home, Sparkles, Video, Images, Settings } from 'lucide-react';

function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const linkClasses = (path: string) =>
    `flex flex-col items-center gap-2 p-3 rounded-xl transition-colors duration-200 group ${
      isActive(path)
        ? 'text-white bg-white/10 shadow-md backdrop-blur-md backdrop-saturate-150'
        : 'text-white hover:text-white hover:bg-white/5 hover:border-white/10 hover:shadow-sm dark:text-gray-400 dark:hover:text-white'
    }`;

  const iconClasses =
    'h-5 w-5 transition-all duration-200 ease-out group-hover:scale-110';

  return (
    <div className="sidebar m-4 flex w-36 flex-col justify-between rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md backdrop-saturate-150 dark:border-white/5">
      <div className="mt-2 flex flex-col gap-4">
        <Link to="/home" className={linkClasses('/home')}>
          <Home
            className={`${iconClasses} `}
            strokeWidth={isActive('/home') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">Home</span>
        </Link>

        <Link to="/ai-tagging" className={linkClasses('/ai-tagging')}>
          <Sparkles
            className={`${iconClasses}`}
            strokeWidth={isActive('/ai-tagging') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">AI Tagging</span>
        </Link>

        <Link to="/videos" className={linkClasses('/videos')}>
          <Video
            className={`${iconClasses} `}
            strokeWidth={isActive('/videos') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">Videos</span>
        </Link>

        <Link to="/albums" className={linkClasses('/albums')}>
          <Images
            className={`${iconClasses} `}
            strokeWidth={isActive('/albums') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">Albums</span>
        </Link>
      </div>

      <Link to="/settings" className={linkClasses('/settings')}>
        <Settings
          className={`${iconClasses} group-hover:rotate-90`}
          strokeWidth={isActive('/settings') ? 2.5 : 2}
        />
        <span className="text-sm font-medium">Settings</span>
      </Link>
    </div>
  );
}

export default Sidebar;
