import type React from 'react';
import { useState, useRef, useEffect } from 'react';
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

interface NetflixStylePlayerProps {
  videoSrc: string;
  title: string;
  description: string;
}

export default function NetflixStylePlayer({videoSrc}: NetflixStylePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    const showControlsTemporarily = () => {
      setShowControls(true);
      clearTimeout(timeout);
      timeout = setTimeout(() => setShowControls(false), 3000);
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('mousemove', showControlsTemporarily);
      container.addEventListener('mouseenter', showControlsTemporarily);
    }

    return () => {
      if (container) {
        container.removeEventListener('mousemove', showControlsTemporarily);
        container.removeEventListener('mouseenter', showControlsTemporarily);
      }
      clearTimeout(timeout);
    };
  }, []);

  const formatTime = (timeInSeconds: number) => {
    const hours = Math.floor(timeInSeconds / 3600);
    const minutes = Math.floor((timeInSeconds % 3600) / 60);
    const seconds = Math.floor(timeInSeconds % 60);
  
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const togglePlay = () => {
    if (videoRef.current) {
      isPlaying ? videoRef.current.pause() : videoRef.current.play();
      setIsPlaying(!isPlaying);
    }
  };

  const handleProgress = () => {
    if (videoRef.current) {
      setProgress((videoRef.current.currentTime / videoRef.current.duration) * 100);
    }
  };

  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current) {
      const progressBar = e.currentTarget;
      const clickPosition = (e.clientX - progressBar.getBoundingClientRect().left) / progressBar.offsetWidth;
      videoRef.current.currentTime = clickPosition * videoRef.current.duration;
    }
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  const skipTime = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds;
    }
  };

  const handleVolumeChange = (newVolume: number[]) => {
    if (videoRef.current) {
      const volumeValue = newVolume[0];
      videoRef.current.volume = volumeValue;
      setVolume(volumeValue);
      setIsMuted(volumeValue === 0);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const newMuteState = !isMuted;
      videoRef.current.muted = newMuteState;
      setIsMuted(newMuteState);
    }
  };

  return (
    <div ref={containerRef} className="relative aspect-video w-full bg-black">
      
      {/* Clickable play/pause area above progress bar */}
      <div className="absolute inset-0 flex items-center justify-center" onClick={togglePlay}>
        <video
          ref={videoRef}
          src={videoSrc}
          className="h-full w-full"
          onTimeUpdate={handleProgress}
          preload="auto"
        />
       
      </div>

      
      
      {/* Progress Bar */}
      <div className={`absolute bottom-16 left-0 right-0 px-4 transition-opacity ${showControls ? 'opacity-100' : 'opacity-0'}`}>
     
        <div className="h-1 w-full cursor-pointer bg-gray-600" onClick={handleProgressBarClick}>
          <div className="h-full bg-red-600" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Controls */}
      <div className={`absolute bottom-4 left-0 right-0 flex items-center justify-between px-4 transition-opacity ${showControls ? 'opacity-100' : 'opacity-0'}`}>
        <div className="flex items-center space-x-4">
          <button onClick={() => skipTime(-10)} className="p-2 text-white"><Rewind size={24} /></button>
          <button onClick={togglePlay} className="p-2 text-white">{isPlaying ? <Pause size={24} /> : <Play size={24} />}</button>
          <button onClick={() => skipTime(10)} className="p-2 text-white"><FastForward size={24} /></button>
          <div className='text-white'>
            {formatTime(videoRef.current?.currentTime ?? 0) +" / " + 
            formatTime(videoRef.current?.duration ?? 0)}
          </div>
        </div>

        {/* Volume and Fullscreen */}
        <div className="flex items-center space-x-4">
          <button onClick={toggleMute} className="text-white">{isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />}</button>
          <Slider min={0} max={1} step={0.01} value={[isMuted ? 0 : volume]} onValueChange={handleVolumeChange} className="w-24" />
          <button onClick={toggleFullScreen} className="text-white">{isFullscreen ? <Minimize2 size={24} /> : <Maximize2 size={24} />}</button>
        </div>
      </div>
    </div>
  );
}
