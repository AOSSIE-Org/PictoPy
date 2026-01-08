import { useRef, useState } from "react";
import { useIntersectionObserver } from "../../hooks/useIntersectionObserver";

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholder?: string;
  rootMargin?: string;
  threshold?: number;
}

export function LazyImage({
  src,
  alt,
  className = "",
  placeholder,
  rootMargin = "200px",
  threshold = 0.1,
}: LazyImageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isVisible = useIntersectionObserver(containerRef, {
    rootMargin,
    threshold,
  });

  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
    >
      {/* Skeleton loader */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 animate-pulse bg-muted" />
      )}

      {/* Image */}
      {isVisible && !hasError && (
        <img
          src={src}
          alt={alt}
          className={`h-full w-full object-cover transition-opacity duration-300 ${
            isLoaded ? "opacity-100" : "opacity-0"
          }`}
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
        />
      )}

      {/* Error state */}
      {hasError && (
        <div className="flex h-full w-full items-center justify-center bg-muted text-xs text-muted-foreground">
          Failed to load image
        </div>
      )}
    </div>
  );
}
