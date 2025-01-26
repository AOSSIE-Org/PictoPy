"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Play, Pause, Maximize2, Minimize2, Rewind, FastForward, Volume2, VolumeX } from "lucide-react"
import { Slider } from "@/components/ui/slider"

interface NetflixStylePlayerProps {
  videoSrc: string
  title: string
  description: string
}

export default function NetflixStylePlayer({ videoSrc, title, description }: NetflixStylePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [showControls, setShowControls] = useState(false) // Initially hidden
  const [isFullscreen, setIsFullscreen] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let timeout: NodeJS.Timeout
    const showControlsTemporarily = () => {
      setShowControls(true)
      clearTimeout(timeout)
      timeout = setTimeout(() => setShowControls(false), 3000) // Hide after 3 seconds
    }

    const container = containerRef.current
    if (container) {
      container.addEventListener("mousemove", showControlsTemporarily)
      container.addEventListener("mouseenter", showControlsTemporarily)
    }

    return () => {
      if (container) {
        container.removeEventListener("mousemove", showControlsTemporarily)
        container.removeEventListener("mouseenter", showControlsTemporarily)
      }
      clearTimeout(timeout)
    }
  }, [])

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleProgress = () => {
    if (videoRef.current) {
      const progress = (videoRef.current.currentTime / videoRef.current.duration) * 100
      setProgress(progress)
    }
  }

  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current) {
      const progressBar = e.currentTarget
      const clickPosition = (e.clientX - progressBar.getBoundingClientRect().left) / progressBar.offsetWidth
      videoRef.current.currentTime = clickPosition * videoRef.current.duration
    }
  }

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const skipTime = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds
    }
  }

  const handleVolumeChange = (newVolume: number[]) => {
    if (videoRef.current) {
      const volumeValue = newVolume[0]
      videoRef.current.volume = volumeValue
      setVolume(volumeValue)
      setIsMuted(volumeValue === 0)
    }
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
      if (isMuted) {
        videoRef.current.volume = volume
      } else {
        setVolume(videoRef.current.volume)
        videoRef.current.volume = 0
      }
    }
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange)
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange)
    }
  }, [])

  const handleVideoClick = (e: React.MouseEvent) => {
    // Prevent video click from interfering with button click
    e.stopPropagation()
    togglePlay()
  }

  const handleContainerClick = (e: React.MouseEvent) => {
    // Get container dimensions
    const container = containerRef.current
    if (!container) return

    const { left, right, top, bottom, width, height } = container.getBoundingClientRect()

    // Define the clickable middle area (e.g., 40% of the width in the middle of the screen)
    const middleAreaWidth = width * 0.4
    const middleAreaHeight = height * 0.4
    const centerX = (left + right) / 2
    const centerY = (top + bottom) / 2

    const clickX = e.clientX
    const clickY = e.clientY

    // Check if click is within the middle area
    const withinX = clickX >= centerX - middleAreaWidth / 2 && clickX <= centerX + middleAreaWidth / 2
    const withinY = clickY >= centerY - middleAreaHeight / 2 && clickY <= centerY + middleAreaHeight / 2

    if (withinX && withinY) {
      togglePlay()
      setShowControls(true) // Show controls when clicked
    }
  }

  return (
    <div ref={containerRef} className="relative w-full aspect-video z-10 bg-black" onClick={handleContainerClick}>
      <video
        ref={videoRef}
        src={videoSrc}
        className="w-full h-full"
        onTimeUpdate={handleProgress}
        onClick={handleVideoClick}  // Updated to handle video click separately
      />

      {/* Center Play/Pause Button */}
    {/* Center Play/Pause Button */}
<div className={`absolute inset-0 flex justify-center items-center ${!isPlaying ? "opacity-100" : "opacity-0"}`}>
  <button
    onClick={togglePlay}
    className="text-white  rounded-full p-4 focus:outline-none  transition-colors"
    aria-label={isPlaying ? "Pause" : "Play"}
  >
    {isPlaying ? <Pause size={40} /> : <Play size={40} />}
  </button>
</div>


      {/* Overlay */}
      <div
        className={`absolute inset-0 bg-gradient-to-t from-black/70 to-transparent transition-opacity duration-300 ${showControls ? "opacity-100" : "opacity-0"}`}
      >
        <div className="absolute bottom-16 left-8 text-white">
          <h2 className="text-4xl font-bold mb-2">{title}</h2>
          <p className="text-lg">{description}</p>
        </div>
      </div>

      {/* Controls */}
      <div
        className={`absolute bottom-0 left-0 right-0 p-4  transition-opacity duration-300 ${showControls ? "opacity-100" : "opacity-0"}`}
      >
        <div className="flex items-center space-x-4">
          <button
            onClick={() => skipTime(-10)}
            className="text-white bg-white/30 rounded-full p-2 focus:outline-none hover:bg-white/50 transition-colors"
            aria-label="Skip back 10 seconds"
          >
            <Rewind size={24} />
          </button>
          <button
            onClick={togglePlay}
            className="text-white bg-white/30 rounded-full p-2 focus:outline-none hover:bg-white/50 transition-colors"
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>
          <button
            onClick={() => skipTime(10)}
            className="text-white bg-white/30 rounded-full p-2 focus:outline-none hover:bg-white/50 transition-colors"
            aria-label="Skip forward 10 seconds"
          >
            <FastForward size={24} />
          </button>
          <div className="flex-grow">
            <div
              className="bg-gray-600 h-1 rounded-full overflow-hidden cursor-pointer"
              onClick={handleProgressBarClick}
            >
              <div className="bg-red-600 h-full" style={{ width: `${progress}%` }} />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleMute}
              className="text-white focus:outline-none"
              aria-label={isMuted ? "Unmute" : "Mute"}
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
            />
          </div>
          <button
            onClick={toggleFullScreen}
            className="text-white focus:outline-none"
            aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
          >
            {isFullscreen ? <Minimize2 size={24} /> : <Maximize2 size={24} />}
          </button>
        </div>
      </div>
    </div>
  )
}