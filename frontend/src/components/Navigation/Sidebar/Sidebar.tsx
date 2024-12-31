import { Link } from 'react-router-dom';
import { Home, Sparkles, Video, Images, Settings as SettingsIcon } from 'react-icons'; // Adjust the imports based on your icons
import { useState } from 'react';

const Sidebar = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Function to handle mouse enter and leave for expanding and collapsing the sidebar
  const handleMouseEnter = () => setIsExpanded(true);
  const handleMouseLeave = () => setIsExpanded(false);

  // Function to determine if a link is active based on the current path
  const linkClasses = (path: string) => {
    const isActive = window.location.pathname === path; // Can be replaced with router hook for dynamic routing
    return `flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${isActive ? 'bg-blue-500 text-white' : 'text-gray-600'}`;
  };

  // Icon styling classes
  const iconClasses = 'h-5 w-5 transition-transform duration-200 ease-out group-hover:scale-110';

  return (
    <div
      className={`relative sidebar bg-theme-light dark:bg-gray-800 text-gray-900 dark:text-gray-200 m-4 flex flex-col justify-between rounded-2xl border border-gray-300 dark:border-gray-700 p-4 shadow-md transition-all duration-300 ${isExpanded ? 'w-48' : 'w-16'}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="mt-2 flex flex-col gap-2">
        {[ 
          { path: '/home', label: 'Home', Icon: Home }, 
          { path: '/ai-tagging', label: 'AI Tagging', Icon: Sparkles }, 
          { path: '/videos', label: 'Videos', Icon: Video }, 
          { path: '/albums', label: 'Albums', Icon: Images },
          { path: '/settings', label: 'Settings', Icon: SettingsIcon }, // Add the Settings link here
        ].map(({ path, label, Icon }) => (
          <Link
            to={path}
            className={linkClasses(path)}
            tabIndex={0}
            aria-label={label}
            key={path}
          >
            <Icon
              className={`${iconClasses} ${window.location.pathname === path ? 'scale-110 text-gray-800' : ''}`}
              strokeWidth={window.location.pathname === path ? 2.5 : 1.5}
            />
            <span
              className={`whitespace-nowrap text-sm font-medium transition-opacity duration-200 ${isExpanded ? 'opacity-100' : 'opacity-0'}`}
            >
              {label}
            </span>
            {/* Ripple effect on hover */}
            <span
              className={`absolute inset-0 rounded-lg bg-gray-200 opacity-0 transition-opacity duration-300 group-hover:opacity-10 ${window.location.pathname === path ? 'opacity-20' : ''}`}
            ></span>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
