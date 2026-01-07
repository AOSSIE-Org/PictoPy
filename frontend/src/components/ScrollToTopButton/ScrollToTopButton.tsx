import { useEffect, useState } from 'react';

type ScrollToTopButtonProps = {
  scrollContainerRef?: React.RefObject<HTMLElement | null>;
  threshold?: number;
};

export const ScrollToTopButton = ({
  scrollContainerRef,
  threshold = 300,
}: ScrollToTopButtonProps) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const scroller = scrollContainerRef?.current || window;

    const handleScroll = () => {
      const scrollTop =
        scroller instanceof Window
          ? window.scrollY
          : scroller.scrollTop;

      setVisible(scrollTop > threshold);
    };

    scroller.addEventListener('scroll', handleScroll);
    return () => scroller.removeEventListener('scroll', handleScroll);
  }, [scrollContainerRef, threshold]);

  const scrollToTop = () => {
    const scroller = scrollContainerRef?.current;

    if (scroller) {
      scroller.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  if (!visible) return null;

  return (
    <button
      onClick={scrollToTop}
      aria-label="Scroll to top"
      className="
        fixed top-35 right-15 z-50
        rounded-full bg-primary p-3
        text-white shadow-lg
        transition-all duration-300
        hover:scale-110 hover:shadow-xl
      "
    >
      ↑
    </button>
  );
};
