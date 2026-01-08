import { useEffect, useState, RefObject } from "react";

interface IntersectionOptions {
  root?: Element | null;
  rootMargin?: string;
  threshold?: number;
}

/**
 * Hook to detect when an element enters the viewport
 */
export function useIntersectionObserver(
  ref: RefObject<Element | null>,
  options: IntersectionOptions = {}
) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || isVisible) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(element);
        }
      },
      {
        root: options.root ?? null,
        rootMargin: options.rootMargin ?? "200px",
        threshold: options.threshold ?? 0.1,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [ref, isVisible, options.root, options.rootMargin, options.threshold]);

  return isVisible;
}
