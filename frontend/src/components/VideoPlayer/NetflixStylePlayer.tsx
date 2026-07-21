import type React from 'react';
import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import {
  Play,
  Pause,
  Maximize2,
  Minimize2,
  Rewind,
  FastForward,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { Slider } from '../../components/ui/Slider';
import { convertFileSrc } from '@tauri-apps/api/core';

interface NetflixStylePlayerProps {
  videoSrc: string;
  title: string;
  description: string;
  autoPlay?: boolean;
  onEnded?: () => void;
}

const CONTROLS_HIDE_DELAY_MS = 3000;
// Small delay before autoplay so the open/navigation transition settles first,
// mirroring how streaming apps ease into playback rather than starting instantly.
const AUTO_PLAY_DELAY_MS = 500;
// Width of the seek-bar hover preview, used to keep it inside the bar's bounds.
const SEEK_PREVIEW_WIDTH_PX = 160;
// Don't re-seek the preview for sub-threshold cursor moves.
const SEEK_PREVIEW_STEP_S = 0.2;

export default function NetflixStylePlayer({
  videoSrc,
  title,
  description,
  autoPlay = false,
  onEnded,
}: NetflixStylePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFocusWithin, setIsFocusWithin] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [previewTime, setPreviewTime] = useState<number | null>(null);
  const [previewLeft, setPreviewLeft] = useState(0);
  // Mounted lazily on first scrub so users who never hover pay no decode cost,
  // then kept mounted so subsequent hovers are instant.
  const [isPreviewMounted, setIsPreviewMounted] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const previewVideoRef = useRef<HTMLVideoElement>(null);
  const seekBarRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hideControlsTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const resolvedSrc = useMemo(() => convertFileSrc(videoSrc), [videoSrc]);

  useEffect(() => {
    setHasError(false);
    setPreviewTime(null);
  }, [resolvedSrc]);

  // Seek the preview after render so it also works on the very first hover,
  // when the element has only just been mounted and the ref isn't set yet.
  useEffect(() => {
    const preview = previewVideoRef.current;
    if (previewTime === null || !preview) return;
    if (Math.abs(preview.currentTime - previewTime) > SEEK_PREVIEW_STEP_S) {
      preview.currentTime = previewTime;
    }
  }, [previewTime, isPreviewMounted]);

  // Autoplay after a short delay. Opening/navigating is a user gesture, so
  // playback is normally allowed; if the browser blocks it, play() rejects and
  // the video simply stays paused with controls visible.
  useEffect(() => {
    if (!autoPlay) return;
    const timer = setTimeout(() => {
      videoRef.current?.play().catch(() => {});
    }, AUTO_PLAY_DELAY_MS);
    return () => clearTimeout(timer);
  }, [autoPlay, resolvedSrc]);

  // Always visible while paused; while playing, visible on hover/touch/focus only.
  const controlsVisible = !isPlaying || showControls || isFocusWithin;

  const revealControlsTemporarily = useCallback(() => {
    setShowControls(true);
    clearTimeout(hideControlsTimeoutRef.current);
    hideControlsTimeoutRef.current = setTimeout(
      () => setShowControls(false),
      CONTROLS_HIDE_DELAY_MS,
    );
  }, []);

  const hideControlsNow = useCallback(() => {
    clearTimeout(hideControlsTimeoutRef.current);
    setShowControls(false);
  }, []);

  useEffect(() => {
    return () => clearTimeout(hideControlsTimeoutRef.current);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore shortcuts while a control is focused, to avoid double-firing.
      const activeEl = document.activeElement;
      if (
        activeEl instanceof HTMLElement &&
        activeEl.closest(
          'button, input, textarea, select, a[href], [contenteditable="true"], [role="slider"]',
        )
      ) {
        return;
      }

      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlay();
          revealControlsTemporarily();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          skipTime(-10);
          revealControlsTemporarily();
          break;
        case 'ArrowRight':
          e.preventDefault();
          skipTime(10);
          revealControlsTemporarily();
          break;
        case 'm':
        case 'M':
          e.preventDefault();
          toggleMute();
          revealControlsTemporarily();
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          toggleFullScreen();
          revealControlsTemporarily();
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === containerRef.current);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const formatTime = (timeInSeconds: number) => {
    if (!Number.isFinite(timeInSeconds)) {
      return '0:00';
    }
    const hours = Math.floor(timeInSeconds / 3600);
    const minutes = Math.floor((timeInSeconds % 3600) / 60);
    const seconds = Math.floor(timeInSeconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().catch(() => {});
    } else {
      video.pause();
    }
  };

  const handleProgress = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      setProgress(
        videoRef.current.duration
          ? (videoRef.current.currentTime / videoRef.current.duration) * 100
          : 0,
      );
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleDurationChange = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current) {
      const progressBar = e.currentTarget;
      const clickPosition =
        (e.clientX - progressBar.getBoundingClientRect().left) /
        progressBar.offsetWidth;
      const rawTime = clickPosition * videoRef.current.duration;
      const maxTime = Number.isFinite(videoRef.current.duration)
        ? videoRef.current.duration
        : 0;
      const newTime = Math.min(Math.max(rawTime, 0), maxTime);
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  const skipTime = (seconds: number) => {
    if (videoRef.current) {
      const rawTime = videoRef.current.currentTime + seconds;
      const maxTime = Number.isFinite(videoRef.current.duration)
        ? videoRef.current.duration
        : 0;
      const newTime = Math.min(Math.max(rawTime, 0), maxTime);
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleVolumeChange = (newVolume: number[]) => {
    if (videoRef.current) {
      const volumeValue = newVolume[0];
      videoRef.current.volume = volumeValue;
      videoRef.current.muted = volumeValue === 0;
      setVolume(volumeValue);
      setIsMuted(volumeValue === 0);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const newMuteState = !videoRef.current.muted;
      videoRef.current.muted = newMuteState;
      setIsMuted(newMuteState);
    }
  };

  /** Maps the cursor position over the seek bar to a timestamp and seeks the
   *  hidden preview video to that frame. */
  const handleSeekHover = (e: React.MouseEvent<HTMLDivElement>) => {
    const bar = seekBarRef.current;
    const video = videoRef.current;
    if (!bar || !video) return;

    const maxTime = Number.isFinite(video.duration) ? video.duration : 0;
    if (maxTime <= 0) return;

    const { left, width } = bar.getBoundingClientRect();
    if (width <= 0) return;

    const ratio = Math.min(Math.max((e.clientX - left) / width, 0), 1);
    const time = ratio * maxTime;

    // Keep the preview inside the bar instead of spilling off either end.
    const half = SEEK_PREVIEW_WIDTH_PX / 2;
    const clampMax = Math.max(half, width - half);
    setPreviewLeft(Math.min(Math.max(ratio * width, half), clampMax));
    setPreviewTime(time);
  };

  const handleSeekEnter = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsPreviewMounted(true);
    handleSeekHover(e);
  };

  const handleSeekBarKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const video = videoRef.current;
    if (!video) return;
    const maxTime = Number.isFinite(video.duration) ? video.duration : 0;

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowRight':
        e.preventDefault();
        e.stopPropagation();
        skipTime(e.key === 'ArrowLeft' ? -5 : 5);
        break;
      case 'Home':
        e.preventDefault();
        e.stopPropagation();
        video.currentTime = 0;
        setCurrentTime(0);
        break;
      case 'End':
        e.preventDefault();
        e.stopPropagation();
        video.currentTime = maxTime;
        setCurrentTime(maxTime);
        break;
      default:
        break;
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative aspect-video w-full bg-black"
      onMouseMove={revealControlsTemporarily}
      onMouseEnter={revealControlsTemporarily}
      onMouseLeave={() => isPlaying && hideControlsNow()}
      onTouchStart={revealControlsTemporarily}
      onFocus={() => {
        setIsFocusWithin(true);
        revealControlsTemporarily();
      }}
      onBlur={(e) => {
        // Only clear when focus leaves the player, not between controls.
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
          setIsFocusWithin(false);
        }
      }}
    >
      {/* Clickable play/pause area above progress bar */}
      <div
        className="absolute inset-0 flex items-center justify-center"
        onClick={togglePlay}
      >
        <video
          ref={videoRef}
          src={resolvedSrc}
          className="h-full w-full"
          onTimeUpdate={handleProgress}
          onLoadedMetadata={handleLoadedMetadata}
          onDurationChange={handleDurationChange}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => {
            setIsPlaying(false);
            onEnded?.();
          }}
          onError={() => setHasError(true)}
          preload="auto"
        />
        {hasError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/90 text-center">
            <p className="text-lg font-semibold text-white">
              This video cannot be played
            </p>
            <p className="max-w-md text-sm text-gray-400">
              The file may use a codec that is not supported by the built-in
              player.
            </p>
          </div>
        )}
      </div>

      {/* pointer-events-none so it never steals play/pause clicks */}
      {(title || description) && (
        <div
          className={`pointer-events-none absolute top-0 right-0 left-0 bg-gradient-to-b from-black/80 to-transparent px-6 pt-6 pb-16 transition-opacity ${
            controlsVisible ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {title && (
            <h2 className="text-xl font-semibold text-white">{title}</h2>
          )}
          {description && (
            <p className="mt-1 max-w-2xl text-sm text-gray-300">
              {description}
            </p>
          )}
        </div>
      )}

      {/* Progress Bar */}
      <div
        className={`absolute right-0 bottom-16 left-0 px-4 transition-opacity ${
          controlsVisible
            ? 'pointer-events-auto opacity-100'
            : 'pointer-events-none opacity-0'
        }`}
      >
        <div className="relative">
          {/* Hover preview: a second, muted video seeked to the hovered frame */}
          {isPreviewMounted && (
            <div
              className={`pointer-events-none absolute bottom-3 z-10 -translate-x-1/2 transition-opacity duration-150 ${
                previewTime !== null ? 'opacity-100' : 'opacity-0'
              }`}
              style={{ left: `${previewLeft}px` }}
              data-testid="seek-preview"
            >
              <video
                ref={previewVideoRef}
                src={resolvedSrc}
                muted
                playsInline
                preload="metadata"
                tabIndex={-1}
                aria-hidden="true"
                className="h-24 w-40 rounded-md border border-white/20 bg-black object-contain shadow-lg"
              />
              <div className="mt-1 text-center text-xs font-medium text-white">
                {formatTime(previewTime ?? 0)}
              </div>
            </div>
          )}

          {/* py-2/-my-2 widens the pointer target without moving the 1px bar */}
          <div
            className="-my-2 cursor-pointer py-2"
            onClick={handleProgressBarClick}
            onMouseEnter={handleSeekEnter}
            onMouseMove={handleSeekHover}
            onMouseLeave={() => setPreviewTime(null)}
          >
            <div
              ref={seekBarRef}
              role="slider"
              tabIndex={0}
              aria-label="Seek"
              aria-valuemin={0}
              aria-valuemax={Number.isFinite(duration) ? duration : 0}
              aria-valuenow={currentTime}
              aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
              className="h-1 w-full bg-gray-600 focus-visible:ring-2 focus-visible:ring-white focus-visible:outline-hidden"
              onKeyDown={handleSeekBarKeyDown}
            >
              <div
                className="h-full bg-red-600"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div
        className={`absolute right-0 bottom-4 left-0 flex items-center justify-between px-4 transition-opacity ${
          controlsVisible
            ? 'pointer-events-auto opacity-100'
            : 'pointer-events-none opacity-0'
        }`}
      >
        <div className="flex items-center space-x-4">
          <button
            onClick={() => skipTime(-10)}
            className="p-2 text-white"
            aria-label="Rewind 10 seconds"
          >
            <Rewind size={24} />
          </button>
          <button
            onClick={togglePlay}
            className="p-2 text-white"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>
          <button
            onClick={() => skipTime(10)}
            className="p-2 text-white"
            aria-label="Fast forward 10 seconds"
          >
            <FastForward size={24} />
          </button>
          <div className="text-white">
            {formatTime(currentTime) + ' / ' + formatTime(duration)}
          </div>
        </div>

        {/* Volume and Fullscreen */}
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleMute}
            className="text-white"
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />}
          </button>
          <Slider
            min={0}
            max={1}
            step={0.01}
            value={[isMuted ? 0 : volume]}
            onValueChange={handleVolumeChange}
            className="w-24"
            aria-label="Volume"
          />
          <button
            onClick={toggleFullScreen}
            className="text-white"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? <Minimize2 size={24} /> : <Maximize2 size={24} />}
          </button>
        </div>
      </div>
    </div>
  );
}
