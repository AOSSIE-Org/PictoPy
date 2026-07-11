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
}

const CONTROLS_HIDE_DELAY_MS = 3000;

export default function NetflixStylePlayer({
  videoSrc,
  title,
  description,
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
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hideControlsTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const resolvedSrc = useMemo(() => convertFileSrc(videoSrc), [videoSrc]);

  // Netflix-style behaviour: controls always show while paused; while
  // playing they're only shown temporarily (hover/touch) and stay visible
  // as long as keyboard focus remains inside the player. Hidden controls
  // must not remain interactive (pointer-events must follow).
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
      // Ignore global shortcuts while an interactive control is focused,
      // otherwise Space/arrows would both activate the control natively
      // and fire the shortcut (e.g. Space on Play toggling playback twice).
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
        // Only clear when focus leaves the player entirely, not when it
        // moves between controls inside it.
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
          onEnded={() => setIsPlaying(false)}
          preload="auto"
        />
      </div>

      {/* Title / description overlay. Non-interactive (pointer-events-none)
          so it never steals clicks from the play/pause area beneath it. */}
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
        <div
          role="slider"
          tabIndex={0}
          aria-label="Seek"
          aria-valuemin={0}
          aria-valuemax={Number.isFinite(duration) ? duration : 0}
          aria-valuenow={currentTime}
          aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
          className="h-1 w-full cursor-pointer bg-gray-600 focus-visible:ring-2 focus-visible:ring-white focus-visible:outline-hidden"
          onClick={handleProgressBarClick}
          onKeyDown={handleSeekBarKeyDown}
        >
          <div
            className="h-full bg-red-600"
            style={{ width: `${progress}%` }}
          />
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
