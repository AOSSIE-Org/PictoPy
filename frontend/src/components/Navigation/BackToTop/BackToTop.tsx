import { useEffect, useState } from 'react';

const BackToTop = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const checkScroll = () => {
      const anyScrolled = Array.from(document.querySelectorAll('*')).some(el => 
        el.scrollTop > 0
      );
      setIsVisible(anyScrolled);
    };

    window.addEventListener('scroll', checkScroll);
    document.addEventListener('scroll', checkScroll);
    const interval = setInterval(checkScroll, 100);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('scroll', checkScroll);
      document.removeEventListener('scroll', checkScroll);
    };
  }, []);

  const handleClick = () => {
    // Same scroll logic as above
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
      if (el.scrollTop > 0) {
        (el as HTMLElement).scrollTop = 0;
      }
    });
  };

  if (!isVisible) return null;

  return (
    <button
      onClick={handleClick}
      type="button"
      aria-label="Back to top"
      className="fixed bottom-8 right-8 z-50 w-12 h-12 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-110 flex items-center justify-center text-xl font-bold"
    >
      ↑
    </button>
  );
};

export default BackToTop;
