import { Link, useLocation } from 'react-router-dom';
import { Home, Sparkles, Video, Images, Settings } from 'lucide-react';

function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const linkClasses = (path: string) =>
    `flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-200 ${
      isActive(path)
        ? 'text-[#6465F3] bg-[#6465F3]/10 shadow-lg shadow-[#6465F3]/10'
        : 'text-white hover:text-[#6465F3] hover:bg-[#6465F3]/5 dark:text-gray-400 dark:hover:text-[#6465F3]'
    }`;

  return (
    <div className="sidebar m-4 flex w-40 flex-col justify-between rounded-2xl border border-gray-700/50 bg-[#333333] p-4 dark:border-gray-700/50">
      <div className="mt-2 flex flex-col gap-4">
        <Link to="/home" className={linkClasses('/home')}>
          <Home
            className="h-5 w-5 transition-transform duration-200 ease-in-out group-hover:scale-110"
            strokeWidth={isActive('/home') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">Home</span>
        </Link>

        <Link to="/ai-tagging" className={linkClasses('/ai-tagging')}>
          <Sparkles
            className="h-5 w-5 transition-transform duration-200 ease-in-out group-hover:scale-110"
            strokeWidth={isActive('/ai-tagging') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">AI Tagging</span>
        </Link>

        <Link to="/videos" className={linkClasses('/videos')}>
          <Video
            className="h-5 w-5 transition-transform duration-200 ease-in-out group-hover:scale-110"
            strokeWidth={isActive('/videos') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">Videos</span>
        </Link>

        <Link to="/albums" className={linkClasses('/albums')}>
          <Images
            className="h-5 w-5 transition-transform duration-200 ease-in-out group-hover:scale-110"
            strokeWidth={isActive('/albums') ? 2.5 : 2}
          />
          <span className="text-sm font-medium">Albums</span>
        </Link>
      </div>

      <Link to="/settings" className={linkClasses('/settings')}>
        <Settings
          className="h-5 w-5 transition-transform duration-200 ease-in-out group-hover:scale-110"
          strokeWidth={isActive('/settings') ? 2.5 : 2}
        />
        <span className="text-sm font-medium">Settings</span>
      </Link>
    </div>
  );
}

export default Sidebar;
