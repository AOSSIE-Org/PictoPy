import { Link, useLocation } from 'react-router-dom';
import { Home, Sparkles, Video, Images, Settings } from 'lucide-react';
import { useState } from 'react';

function Sidebar() {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);

  
  const isActive = (path) => location.pathname === path;

  
  const linkClasses = (path) => {
    const baseClasses = 'group relative flex items-center gap-3 p-3 rounded-lg overflow-hidden border transition-all duration-300 ease-in-out';

    const activeClasses = 'bg-gray-200 text-gray-800 border-gray-500';
    const inactiveClasses = 'bg-transparent hover:bg-gray-50 text-gray-600 border-transparent shadow-sm hover:shadow-md';

    return `${baseClasses} ${isActive(path) ? activeClasses : inactiveClasses}`;
  };

  
  const iconClasses = 'h-5 w-5 transition-transform duration-200 ease-in-out group-hover:scale-110';
  const activeIconClasses = 'scale-110 text-gray-800';

  
  const handleMouseEnter = () => setIsExpanded(true);
  const handleMouseLeave = () => setIsExpanded(false);

  return (
    <div
      className={`relative sidebar bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-200 m-4 flex flex-col justify-between rounded-2xl border border-gray-300 dark:border-gray-700 p-4 shadow-md transition-all duration-300 ${isExpanded ? 'w-48' : 'w-16'}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      
      <div className="mt-2 flex flex-col gap-2">
        {[ 
          { path: '/home', label: 'Home', Icon: Home }, 
          { path: '/ai-tagging', label: 'AI Tagging', Icon: Sparkles }, 
          { path: '/videos', label: 'Videos', Icon: Video }, 
          { path: '/albums', label: 'Albums', Icon: Images },
        ].map(({ path, label, Icon }) => (
          <Link
            to={path}
            className={linkClasses(path)}
            tabIndex={0}
            aria-label={label}
            key={path}
          >
            <Icon
              className={`${iconClasses} ${isActive(path) ? activeIconClasses : ''}`}
              strokeWidth={isActive(path) ? 2.5 : 1.5}
            />
            <span
              className={`whitespace-nowrap text-sm font-medium transition-opacity duration-200 ${isExpanded ? 'opacity-100' : 'opacity-0'}`}
            >
              {label}
            </span>
            {/* Ripple effect on hover : when user hover upon it there is suttle effect */}
            <span
              className={`absolute inset-0 rounded-lg bg-gray-200 opacity-0 transition-opacity duration-300 group-hover:opacity-10 ${isActive(path) ? 'opacity-20' : ''}`}
            ></span>
          </Link>
        ))}
      </div>

      
      <Link
        to="/settings"
        className={linkClasses('/settings')}
        tabIndex={0}
        aria-label="Settings"
      >
        <Settings
          className={`${iconClasses} transform transition-transform group-hover:scale-110 ${isActive('/settings') ? activeIconClasses : ''}`}
          strokeWidth={isActive('/settings') ? 2.5 : 1.5}
        />
        <span
          className={`whitespace-nowrap text-sm font-medium transition-opacity duration-200 ${isExpanded ? 'opacity-100' : 'opacity-0'}`}
        >
          Settings
        </span>
        <span
          className={`absolute inset-0 rounded-lg bg-gray-200 opacity-0 transition-opacity duration-300 group-hover:opacity-10 ${isActive('/settings') ? 'opacity-20' : ''}`}
        ></span>
      </Link>
    </div>
  );
}

export default Sidebar;