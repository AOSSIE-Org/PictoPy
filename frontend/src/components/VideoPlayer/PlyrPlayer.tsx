import { useEffect, useRef } from 'react';
import 'plyr/dist/plyr.css';

interface PlyrPlayerProps {
  src: string;
  title?: string;
  poster?: string;
}

export default function PlyrPlayer({ src, title, poster }: PlyrPlayerProps) {
  const ref = useRef<HTMLVideoElement | null>(null);
  const playerRef = useRef<any>(null);

  useEffect(() => {
    if (!ref.current) return;

    let mounted = true;

    // Dynamically import Plyr to avoid TypeScript module issues
    import('plyr')
      .then((PlyrModule) => {
        if (!mounted || !ref.current) return;

        const Plyr = (PlyrModule as any).default || PlyrModule;

        console.log('Initializing Plyr...', Plyr);

        // Destroy previous instance if any
        if (playerRef.current) {
          playerRef.current.destroy();
        }

        // Initialize Plyr
        try {
          playerRef.current = new Plyr(ref.current, {
            controls: [
              'play-large',
              'play',
              'progress',
              'current-time',
              'mute',
              'volume',
              'captions',
              'settings',
              'pip',
              'airplay',
              'fullscreen',
            ],
            settings: ['captions', 'quality', 'speed', 'loop'],
            // Enable preview thumbnails on hover
            previewThumbnails: { enabled: false }, // Set to true if you have thumbnail sprites
            // Match demo behavior
            tooltips: { controls: true, seek: true },
            keyboard: { focused: true, global: false },
            invertTime: false,
            // Quality options
            quality: {
              default: 720,
              options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240],
            },
            // Speed options
            speed: {
              selected: 1,
              options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
            },
            // Ratio
            ratio: '16:9',
            // Auto-hide controls
            hideControls: true,
            // Click to play
            clickToPlay: true,
          });

          console.log('Plyr initialized successfully', playerRef.current);
        } catch (error) {
          console.error('Failed to initialize Plyr:', error);
        }
      })
      .catch((error) => {
        console.error('Failed to load Plyr module:', error);
      });

    return () => {
      mounted = false;
      if (playerRef.current) {
        playerRef.current.destroy();
      }
      playerRef.current = null;
    };
  }, [src, title]);

  return (
    <div className="plyr-container h-full w-full">
      <video
        ref={ref}
        playsInline
        crossOrigin="anonymous"
        poster={poster}
        controls
        className="h-full w-full"
      >
        <source src={src} type="video/mp4" />
      </video>
    </div>
  );
}
