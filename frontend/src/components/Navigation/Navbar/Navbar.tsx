import React, { useState, useEffect, useCallback } from 'react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { motion } from 'framer-motion';

interface NavbarProps {
  title?: string;
  onNameChange?: (name: string) => void;
}

export function Navbar({ title, onNameChange }: NavbarProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(title || '');
  const [showPlaceholder, setShowPlaceholder] = useState(!title);

  // Handle initial load and localStorage
  useEffect(() => {
    const storedName = localStorage.getItem('pictopy-username');
    if (storedName) {
      setName(storedName);
      setShowPlaceholder(false);
    }
  }, []);

  const handleNameSubmit = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        const inputValue = (e.target as HTMLInputElement).value.trim();
        if (inputValue) {
          setName(inputValue);
          setShowPlaceholder(false);
          setIsEditing(false);
          localStorage.setItem('pictopy-username', inputValue);
          onNameChange?.(inputValue);
        }
      }
    },
    [onNameChange],
  );

  const handleNameClick = useCallback(() => {
    if (!isEditing) {
      setIsEditing(true);
    }
  }, [isEditing]);

  const handleBlur = useCallback(
    (e: React.FocusEvent<HTMLInputElement>) => {
      const inputValue = e.target.value.trim();
      if (inputValue) {
        setName(inputValue);
        setShowPlaceholder(false);
        localStorage.setItem('pictopy-username', inputValue);
        onNameChange?.(inputValue);
      }
      setIsEditing(false);
    },
    [onNameChange],
  );

  return (
    <header className="flex w-full flex-row items-center justify-center align-middle">
      <motion.div
        initial={{ y: -10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="rounded-2xl mb-4 mt-3 flex h-16 w-[90%] transform items-center justify-between border border-gray-200/30 bg-gradient-to-r from-blue-600 to-purple-700 px-4 shadow-lg backdrop-blur-xl backdrop-saturate-200 transition-all duration-300 ease-in-out hover:shadow-blue-500/10 dark:border-white/5 dark:bg-gradient-to-r dark:from-gray-800 dark:to-black sm:w-[70%] sm:px-8 md:w-[55%] md:px-16"
      >
        {/* Logo Section */}
        <div className="flex items-center gap-4">
          <div className="group flex items-center gap-2">
            <motion.img
              whileHover={{ rotate: 10 }}
              src="/PictoPy_Logo.png"
              className="h-8 transition-all duration-300 hover:opacity-90"
              alt="PictoPy Logo"
            />
            <span className="bg-clip-text font-sans text-lg font-bold text-white drop-shadow-md dark:text-white sm:text-xl">
              PictoPy
            </span>
          </div>
        </div>

        {/* Welcome Section and Theme Toggle */}
        <div className="flex items-center gap-4">
          <div className="flex items-center">
            <span className="font-sans text-lg font-medium text-white/90 drop-shadow-sm">
              Welcome{' '}
            </span>
            {isEditing || showPlaceholder ? (
              <input
                type="text"
                placeholder="Enter your name"
                defaultValue={name}
                onKeyDown={handleNameSubmit}
                onBlur={handleBlur}
                className="ml-2 w-32 rounded-lg border border-white/30 bg-white/10 px-3 py-1 text-white placeholder-white/60 backdrop-blur-sm transition-colors duration-200 focus:border-yellow-300 focus:outline-none focus:ring-2 focus:ring-yellow-300/50"
                autoFocus
                aria-label="Enter your name"
              />
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleNameClick}
                className="ml-2 rounded-lg border border-white/20 bg-white/10 px-3 py-0.5 text-white transition-all duration-200 hover:border-white/30 hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-yellow-300/50 focus:ring-offset-2 focus:ring-offset-transparent"
                aria-label="Click to edit name"
              >
                {name || 'User'}
              </motion.button>
            )}
          </div>
          <ThemeToggle />
        </div>
      </motion.div>
    </header>
  );
}

export default Navbar;
