import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import { Button } from './ui/button';

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="hover:bg-gray-200 dark:hover:bg-gray-700"
    >
      {theme === 'light' ? (
        <SunIcon className="text-theme-dark dark:text-theme-light h-5 w-5" />
      ) : (
        <MoonIcon className="text-theme-dark dark:text-theme-light h-5 w-5" />
      )}
    </Button>
  );
};
