import { Link, useLocation } from 'react-router-dom';
import { Home, Sparkles, Video, Images, Settings } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
function Sidebar() 
const Sidebar = () => {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);

  const isActive = (path: string) => location.pathname === path;
  const [MobileNav,SetMobileNav]=useState(false);
  const handleMouseEnter = () => setIsExpanded(true);
  const handleMouseLeave = () => setIsExpanded(false);
  const linkClasses = (path: string) => {
    const baseClasses =
      'group flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-200';
    const activeClasses = isActive(path)
      ? 'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
      : 'text-gray-500 dark:text-gray-300';
    return `${baseClasses} ${activeClasses}`;
  };

  const iconClasses =
    'h-5 w-5 transition-transform duration-200 ease-out group-hover:scale-110';

  return (
    <div>
     <div className='transition-transform duration-250 sm:-translate-x-24 focus-visible:ring-orange-300 p-1 w-16 flex justify-center ml-3 '>
        <AlignJustify onClick={()=>{
          if(MobileNav){
            SetMobileNav(false)
          }
          else{
            SetMobileNav(true)
          }
        }}></AlignJustify>
      </div>
    <div className={cn('sidebar  text-theme-dark dark:text-theme-light bg-theme-light m-4 flex w-36  max-sm:w-16 flex-col justify-between rounded-2xl border border-gray-300 p-4 backdrop-blur-md backdrop-saturate-150 dark:border-white/10 dark:bg-white/5   transition-transform duration-250',{'max-sm:block max-sm:-translate-x-32':MobileNav})}>
      <div className='mt-2 flex flex-col gap-4'>
        <Link to="/home" className={linkClasses('/home')}>
          <Home
            className={iconClasses}
            strokeWidth={isActive('/home') ? 2.5 : 2}
          />
          <span className="text-sm font-medium max-sm:hidden">Home</span>
        </Link>

        <Link to="/ai-tagging" className={linkClasses('/ai-tagging')}>
          <Sparkles
            className={iconClasses}
            strokeWidth={isActive('/ai-tagging') ? 2.5 : 2}
          />
          <span className="text-sm font-medium max-sm:hidden">AI Tagging</span>
        </Link>

        <Link to="/videos" className={linkClasses('/videos')}>
          <Video
            className={iconClasses}
            strokeWidth={isActive('/videos') ? 2.5 : 2}
          />
          <span className="text-sm font-medium max-sm:hidden">Videos</span>
        </Link>

        <Link to="/albums" className={linkClasses('/albums')}>
          <Images
            className={iconClasses}
            strokeWidth={isActive('/albums') ? 2.5 : 2}
          />
          <span className="text-sm font-medium max-sm:hidden">Albums</span>
        </Link>
      </div>

      <Link to="/settings" className={linkClasses('/settings')}>
        <Settings
          className={`${iconClasses} transform transition-transform group-hover:rotate-90`}
          strokeWidth={isActive('/settings') ? 2.5 : 2}
        />
        <span className="text-sm font-medium max-sm:hidden">Settings</span>
      </Link>
    <div
      className={`sidebar relative bg-theme-light dark:bg-gray-800 text-gray-900 dark:text-gray-200 m-4 flex flex-col justify-between rounded-2xl border border-gray-300 dark:border-gray-700 p-4 shadow-md transition-all duration-300 ${
        isExpanded ? 'w-48' : 'w-16'
      }`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="mt-2 flex flex-col gap-2">
        {[
          { path: '/home', label: 'Home', Icon: Home },
          { path: '/ai-tagging', label: 'AI Tagging', Icon: Sparkles },
          { path: '/videos', label: 'Videos', Icon: Video },
          { path: '/albums', label: 'Albums', Icon: Images },
          { path: '/settings', label: 'Settings', Icon: Settings },
        ].map(({ path, label, Icon }) => (
          <Link
            to={path}
            className={linkClasses(path)}
            tabIndex={0}
            aria-label={label}
            key={path}
          >
            <Icon
              className={`${iconClasses} ${
                isActive(path) ? 'scale-110 text-gray-800' : ''
              }`}
              strokeWidth={isActive(path) ? 2.5 : 1.5}
            />
            <span
              className={`whitespace-nowrap text-sm font-medium transition-opacity duration-200 ${
                isExpanded ? 'opacity-100' : 'opacity-0'
              }`}
            >
              {label}
            </span>
          </Link>
        ))}
      </div>
    </div>
    </div>
  );
};

export default Sidebar;
