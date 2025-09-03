// src/components/SmoothScroll.tsx
import React, { useEffect, useRef } from 'react';

interface SmoothScrollProps {
  children: React.ReactNode;
}

const SmoothScroll: React.FC<SmoothScrollProps> = ({ children }) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [children]);  // Triggered when children change (i.e., new messages)

  return (
    <div
      ref={scrollAreaRef}
      className="flex-grow p-6 overflow-auto"
      style={{
        scrollBehavior: 'smooth',
        maxHeight: 'calc(100vh - 200px)', // Prevents full-page scrolling, adjusts the height
      }}
    >
      {children}
    </div>
  );
};

export default SmoothScroll;
