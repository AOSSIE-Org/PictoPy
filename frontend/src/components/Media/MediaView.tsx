import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { MediaViewProps } from '@/types/Media';
import { selectCurrentViewIndex } from '@/features/imageSelectors';
import { setCurrentViewIndex, closeImageView } from '@/features/imageSlice';

import { ImageViewer } from './ImageViewer';
import { StoryProgressBar } from './StoryProgressBar';

export function MediaView({
  images = [],
  title,
  subtitle,
  onClose,
}: MediaViewProps) {
  const dispatch = useDispatch();
  const currentIndex = useSelector(selectCurrentViewIndex);

  const [paused, setPaused] = useState(false);
  const [visible, setVisible] = useState(true);

  const currentImage = useMemo(
    () => images[currentIndex] ?? null,
    [images, currentIndex],
  );

  /* --------------------------------
     AUTO PLAY (with pause)
  --------------------------------- */
  useEffect(() => {
    if (!images.length || paused) return;

    const timer = setTimeout(() => {
      setVisible(false); // fade out
      setTimeout(() => {
        if (currentIndex < images.length - 1) {
          dispatch(setCurrentViewIndex(currentIndex + 1));
        } else {
          dispatch(closeImageView());
          onClose?.();
        }
        setVisible(true); // fade in
      }, 300);
    }, 4000);

    return () => clearTimeout(timer);
  }, [currentIndex, paused, images.length, dispatch, onClose]);

  /* --------------------------------
     Keyboard support
  --------------------------------- */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') {
        dispatch(
          setCurrentViewIndex(Math.min(currentIndex + 1, images.length - 1)),
        );
      }
      if (e.key === 'ArrowLeft') {
        dispatch(setCurrentViewIndex(Math.max(currentIndex - 1, 0)));
      }
      if (e.key === ' ') {
        e.preventDefault();
        setPaused((p) => !p);
      }
      if (e.key === 'Escape') {
        dispatch(closeImageView());
        onClose?.();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentIndex, images.length, dispatch, onClose]);

  if (!currentImage) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
      {/* Progress bar */}
      <StoryProgressBar
        total={images.length}
        current={currentIndex}
        paused={paused}
      />

      {/* Close */}
      <button
        onClick={() => {
          dispatch(closeImageView());
          onClose?.();
        }}
        className="absolute top-24 left-6 z-50 text-2xl text-white"
      >
        ✕
      </button>

      {/* Pause / Play (CENTERED like Google Photos) */}
      <button
        onClick={() => setPaused((p) => !p)}
        className="absolute top-24 right-6 z-50 -translate-x-1/2 text-xl text-white"
      >
        {paused ? '▶' : '❚❚'}
      </button>

      {/* Title + Date */}
      <div className="absolute top-6 left-20 z-50 text-white">
        {subtitle && <p className="text-xs opacity-70">{subtitle}</p>}
        {title && <h2 className="text-sm font-semibold">{title}</h2>}
      </div>

      {/* STORY CONTAINER (LANDSCAPE) */}
      <div
        className="relative h-[60vh] w-[70vw] max-w-[900px] overflow-hidden rounded-2xl bg-black shadow-2xl"
        onMouseDown={() => setPaused(true)}
        onMouseUp={() => setPaused(false)}
      >
        {/* FADE IMAGE */}
        <div
          className={`absolute inset-0 transition-opacity duration-300 ease-in-out ${
            visible ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <ImageViewer imagePath={currentImage.path} alt="story" rotation={0} />
        </div>

        {/* Click zones */}
        <div
          className="absolute top-0 left-0 h-full w-1/2 cursor-pointer"
          onClick={() =>
            currentIndex > 0 && dispatch(setCurrentViewIndex(currentIndex - 1))
          }
        />
        <div
          className="absolute top-0 right-0 h-full w-1/2 cursor-pointer"
          onClick={() =>
            currentIndex < images.length - 1 &&
            dispatch(setCurrentViewIndex(currentIndex + 1))
          }
        />
      </div>
    </div>
  );
}
