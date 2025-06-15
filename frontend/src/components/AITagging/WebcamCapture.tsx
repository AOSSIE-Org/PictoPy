import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Camera } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { BACKEND_URL } from '@/config/Backend';

interface WebcamCaptureProps {
  onCapture: (matchedPaths: string[], errorMessage?: string) => void;
  onClose: () => void;
}

const GlobalInstanceCount = { count: 0 };

const WebcamCapture: React.FC<WebcamCaptureProps> = ({
  onCapture,
  onClose,
}) => {
  const [isConnecting, setIsConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [facesDetected, setFacesDetected] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const [fps, setFps] = useState<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const framesReceived = useRef<number>(0);
  const instanceId = useRef(++GlobalInstanceCount.count);
  const attemptRef = useRef<number>(0);
  const cleanupFnRef = useRef<(() => void) | null>(null);

  // Generate a unique client ID for each component instance
  const clientId = useRef<string>(uuidv4());

  // Track whether component is mounted
  const isMountedRef = useRef<boolean>(true);

  // Delay sending the "close" message to ensure messages are processed in order
  const sendCloseMessage = async () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      console.log('Sending close action to server');
      try {
        socketRef.current.send(JSON.stringify({ action: 'close' }));
        // Small delay to allow the close message to be sent
        await new Promise((resolve) => setTimeout(resolve, 100));
      } catch (e) {
        console.error('Error sending close message:', e);
      }
    }
  };

  const cleanupResources = async () => {
    console.log(
      `Cleaning up WebSocket resources for instance ${instanceId.current}`,
    );

    try {
      await sendCloseMessage();

      if (socketRef.current) {
        console.log('Closing WebSocket connection');
        socketRef.current.close();
        socketRef.current = null;
      }
    } catch (e) {
      console.error('Error during cleanup:', e);
    }
  };

  const handleClose = async () => {
    console.log('handleClose called');
    await cleanupResources();
    onClose();
  };

  const connectWebSocket = async () => {
    // Don't attempt to connect if component is unmounted
    if (!isMountedRef.current) return () => {};

    // Increment attempt counter for each connection attempt
    attemptRef.current += 1;

    // Create a different client ID for each connection attempt
    const connectionClientId = `${clientId.current}-${attemptRef.current}`;
    console.log(
      `Starting connection attempt #${attemptRef.current} with ID: ${connectionClientId}`,
    );

    setIsConnecting(true);
    setError(null);
    framesReceived.current = 0;

    // Clean up any existing connection - BUT wait for it to complete
    // This fixes the race condition where we're closing the old socket while opening a new one
    if (socketRef.current) {
      console.log(
        'Waiting for previous socket to close before creating a new one',
      );
      await cleanupResources();

      // Small delay to ensure the backend has time to fully clean up
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = BACKEND_URL.replace(/^https?:\/\//, '');
    const wsFullUrl = `${wsProtocol}//${wsUrl}/tag/webcam-feed/${connectionClientId}`;

    console.log(`Connecting to WebSocket at: ${wsFullUrl}`);

    try {
      const socket = new WebSocket(wsFullUrl);
      socketRef.current = socket;

      // Connection timeout 10 seconds
      const connectionTimeout = setTimeout(() => {
        if (!isMountedRef.current || socketRef.current !== socket) return;

        console.log('Connection timeout reached');
        setError('Connection timeout. Please try again.');
        setIsConnecting(false);

        // Close the socket
        try {
          socket.close();
          socketRef.current = null;
        } catch (e) {
          console.error('Error closing socket after timeout:', e);
        }
      }, 10000); // 10 seconds timeout

      socket.onopen = () => {
        console.log(
          `WebSocket connection opened (attempt #${attemptRef.current})`,
        );
        // isConnecting will be set to false when 'connected' event is received
      };

      socket.onmessage = (event) => {
        if (!isMountedRef.current || socketRef.current !== socket) return;

        try {
          const data = JSON.parse(event.data);
          console.log(`Received event: ${data.event}`);

          if (data.event === 'connected') {
            console.log('Camera connected event received');
            setIsConnecting(false);
            clearTimeout(connectionTimeout); // Clear timeout on successful connection
          } else if (data.event === 'frame' && imageRef.current) {
            if (
              framesReceived.current === 0 ||
              framesReceived.current % 30 === 0
            ) {
              console.log(`Received frame #${framesReceived.current}`);
            }

            framesReceived.current++;
            imageRef.current.src = `data:image/jpeg;base64,${data.image}`;
            setFacesDetected(data.faces_detected || 0);
            if (data.fps) setFps(data.fps);
          } else if (data.event === 'error') {
            console.error('Server error:', data.message);
            setError(data.message);
            setIsConnecting(false);
          } else if (data.event === 'search_result') {
            setIsCapturing(false);
            if (data.success) {
              const matchedPaths = data.matches.map((match: any) => match.path);
              onCapture(matchedPaths);
            } else {
              onCapture(
                [],
                data.message || 'No faces detected in captured image',
              );

              setError(data.message || 'No faces detected in captured image');
              setTimeout(() => {
                if (isMountedRef.current) {
                  setError(null);
                }
              }, 3000);
            }
          }
        } catch (err) {
          console.error('Error parsing message:', err);
        }
      };

      socket.onerror = (err) => {
        if (!isMountedRef.current || socketRef.current !== socket) return;

        console.error('WebSocket error:', err);
        setError('Connection error. Please try again.');
        setIsConnecting(false);
        clearTimeout(connectionTimeout);
      };

      socket.onclose = (event) => {
        if (!isMountedRef.current || socketRef.current !== socket) return;

        clearTimeout(connectionTimeout);
        console.log(
          `WebSocket closed: code=${event.code}, reason=${event.reason || 'none'}`,
        );

        if (framesReceived.current === 0) {
          setError(
            'Connection closed before receiving camera feed. Please try again.',
          );
          setIsConnecting(false);
        }
      };

      return () => clearTimeout(connectionTimeout);
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setError('Failed to create connection. Please try again.');
      setIsConnecting(false);
      return () => {};
    }
  };

  useEffect(() => {
    console.log('Component mounted');
    isMountedRef.current = true;
    attemptRef.current = 0;

    (async () => {
      if (isMountedRef.current) {
        const cleanup = await connectWebSocket();

        if (typeof cleanup === 'function') {
          cleanupFnRef.current = cleanup;
        }
      }
    })();

    return () => {
      console.log('Component unmounting');
      isMountedRef.current = false;

      if (typeof cleanupFnRef.current === 'function') {
        cleanupFnRef.current();
      }

      cleanupResources();
    };
  }, []);

  const handleCapture = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      setIsCapturing(true);
      socketRef.current.send(JSON.stringify({ action: 'capture' }));
    }
  };

  const handleRetry = async () => {
    console.log('Retrying connection');
    await connectWebSocket();
  };

  useEffect(() => {
    if (
      error ===
        'Connection closed before receiving camera feed. Please try again.' &&
      attemptRef.current < 3
    ) {
      console.log(
        `Auto-retrying connection (attempt ${attemptRef.current + 1} of 3)...`,
      );

      const retryTimeout = setTimeout(() => {
        if (isMountedRef.current) {
          handleRetry();
        }
      }, 1500);

      return () => clearTimeout(retryTimeout);
    }
  }, [error]);

  return (
    <div className="flex w-full max-w-full flex-col gap-4">
      <div className="relative">
        <div className="w-full overflow-hidden rounded-lg bg-black">
          {isConnecting ? (
            <div className="flex h-[360px] w-full max-w-full items-center justify-center">
              <p className="text-white">Connecting to camera...</p>
            </div>
          ) : error ? (
            <div
              className="flex h-[360px] w-full max-w-full cursor-pointer items-center justify-center bg-red-900/20 p-4 text-center"
              onClick={handleRetry}
            >
              <p className="text-red-200">{error}</p>
            </div>
          ) : (
            <div className="relative w-full">
              <img
                ref={imageRef}
                className="h-[360px] w-full object-cover"
                alt="Webcam feed"
              />
              <div className="absolute top-2 left-2 rounded-full bg-black/60 px-3 py-1 text-sm text-white">
                {facesDetected > 0
                  ? `${facesDetected} ${facesDetected === 1 ? 'face' : 'faces'} detected`
                  : 'No faces detected'}
                {fps && ` • ${fps} FPS`}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between gap-2">
        <Button
          onClick={handleCapture}
          disabled={
            isConnecting || !!error || isCapturing || facesDetected === 0
          }
          className="flex-1 items-center justify-center gap-2"
        >
          <Camera size={18} />
          {isCapturing ? 'Processing...' : 'Capture'}
        </Button>

        <Button
          variant="outline"
          onClick={handleClose}
          className="items-center justify-center"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
};

export default WebcamCapture;
