import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingScreenProps {
  // Control whether the loading screen is shown
  isLoading?: boolean;
  // Choose between full-screen overlay or inline loading
  variant?: 'fullscreen' | 'inline' | 'corner';
  // Optional message to display
  message?: string;
  // Optional callback when clicking outside the loader (for dismissible loaders)
  onOutsideClick?: () => void;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  isLoading = true,
  variant = 'inline',
  message = 'Loading...',
  onOutsideClick,
}) => {
  const [isVisible, setIsVisible] = useState(isLoading);

  useEffect(() => {
    setIsVisible(isLoading);
  }, [isLoading]);

  if (!isVisible) return null;

  // Styles for different variants
  const containerStyles = {
    fullscreen:
      'fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-900 bg-opacity-50',
    inline: 'relative flex flex-col items-center justify-center py-8',
    corner:
      'fixed bottom-4 right-4 z-40 flex items-center gap-2 rounded-lg bg-background p-3 shadow-lg border',
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    // Only trigger if clicking the backdrop itself, not the loader
    if (e.target === e.currentTarget && onOutsideClick) {
      onOutsideClick();
    }
  };

  return (
    <div
      className={containerStyles[variant]}
      onClick={variant === 'fullscreen' ? handleBackdropClick : undefined}
    >
      <div className="flex flex-col items-center">
        <Loader2
          className={`animate-spin ${variant === 'corner' ? 'h-5 w-5' : 'h-10 w-10'}`}
        />
        {message && (
          <p
            className={`mt-2 font-medium ${variant === 'fullscreen' ? 'text-white' : 'text-foreground'}`}
          >
            {message}
          </p>
        )}
      </div>
    </div>
  );
};

export default LoadingScreen;
