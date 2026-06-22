import { render, screen, fireEvent, act } from '@testing-library/react';
import NetflixStylePlayer from '../NetflixStylePlayer';

// Mock Tauri convertFileSrc API
jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

// Mock Slider component to use simple range input for testing
jest.mock('../../ui/Slider', () => ({
  Slider: ({ onValueChange, value, min, max, step }: any) => (
    <input
      data-testid="volume-slider"
      type="range"
      min={min}
      max={max}
      step={step}
      value={value[0]}
      onChange={(e) => onValueChange([parseFloat(e.target.value)])}
    />
  ),
}));

// Mock lucide icons for easy querying
jest.mock('lucide-react', () => ({
  Play: () => <span data-testid="icon-play">Play</span>,
  Pause: () => <span data-testid="icon-pause">Pause</span>,
  Rewind: () => <span data-testid="icon-rewind">Rewind</span>,
  FastForward: () => <span data-testid="icon-fastforward">FastForward</span>,
  Volume2: () => <span data-testid="icon-volume">Volume</span>,
  VolumeX: () => <span data-testid="icon-mute">Mute</span>,
  Maximize2: () => <span data-testid="icon-maximize">Maximize</span>,
  Minimize2: () => <span data-testid="icon-minimize">Minimize</span>,
}));

describe('NetflixStylePlayer', () => {
  let requestFullscreenMock: jest.Mock;
  let exitFullscreenMock: jest.Mock;

  beforeEach(() => {
    // Mock HTMLMediaElement play and pause
    window.HTMLMediaElement.prototype.play = jest
      .fn()
      .mockImplementation(function (this: HTMLVideoElement) {
        const playEvent = new Event('play');
        this.dispatchEvent(playEvent);
        return Promise.resolve();
      });

    window.HTMLMediaElement.prototype.pause = jest
      .fn()
      .mockImplementation(function (this: HTMLVideoElement) {
        const pauseEvent = new Event('pause');
        this.dispatchEvent(pauseEvent);
      });

    requestFullscreenMock = jest.fn();
    exitFullscreenMock = jest.fn();

    HTMLElement.prototype.requestFullscreen = requestFullscreenMock;
    document.exitFullscreen = exitFullscreenMock;

    Object.defineProperty(document, 'fullscreenElement', {
      value: null,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('converts video source using convertFileSrc for Tauri support', () => {
    render(
      <NetflixStylePlayer
        videoSrc="local-path/video.mp4"
        title="Test"
        description="Desc"
      />,
    );
    const video = document.querySelector('video') as HTMLVideoElement;
    expect(video).toBeInTheDocument();
    expect(video.src).toBe('tauri-converted://local-path/video.mp4');
  });

  test('updates isFullscreen state on fullscreenchange event', () => {
    const { container } = render(
      <NetflixStylePlayer
        videoSrc="test-video.mp4"
        title="Test"
        description="Desc"
      />,
    );

    expect(screen.queryByTestId('icon-minimize')).not.toBeInTheDocument();
    expect(screen.getByTestId('icon-maximize')).toBeInTheDocument();

    Object.defineProperty(document, 'fullscreenElement', {
      value: container.firstChild,
      writable: true,
      configurable: true,
    });

    act(() => {
      document.dispatchEvent(new Event('fullscreenchange'));
    });

    expect(screen.getByTestId('icon-minimize')).toBeInTheDocument();
    expect(screen.queryByTestId('icon-maximize')).not.toBeInTheDocument();

    Object.defineProperty(document, 'fullscreenElement', {
      value: null,
      writable: true,
      configurable: true,
    });

    act(() => {
      document.dispatchEvent(new Event('fullscreenchange'));
    });

    expect(screen.queryByTestId('icon-minimize')).not.toBeInTheDocument();
    expect(screen.getByTestId('icon-maximize')).toBeInTheDocument();
  });

  test('renders 0:00 before video metadata is loaded and updates on loadedmetadata', () => {
    render(
      <NetflixStylePlayer
        videoSrc="video.mp4"
        title="Test"
        description="Desc"
      />,
    );

    expect(screen.getByText('0:00 / 0:00')).toBeInTheDocument();

    const video = document.querySelector('video') as HTMLVideoElement;

    Object.defineProperty(video, 'duration', {
      configurable: true,
      value: 125,
    });

    act(() => {
      fireEvent(video, new Event('loadedmetadata'));
    });

    expect(screen.getByText('0:00 / 2:05')).toBeInTheDocument();
  });

  test('volume slider updates volume and unmutes video', () => {
    render(
      <NetflixStylePlayer
        videoSrc="video.mp4"
        title="Test"
        description="Desc"
      />,
    );
    const video = document.querySelector('video') as HTMLVideoElement;

    let setMutedVal = false;
    let setVolumeVal = 1;
    Object.defineProperty(video, 'muted', {
      get: () => setMutedVal,
      set: (val) => {
        setMutedVal = val;
      },
      configurable: true,
    });
    Object.defineProperty(video, 'volume', {
      get: () => setVolumeVal,
      set: (val) => {
        setVolumeVal = val;
      },
      configurable: true,
    });

    const muteBtn = screen.getByTestId('icon-volume').closest('button');
    expect(muteBtn).toBeInTheDocument();

    act(() => {
      fireEvent.click(muteBtn!);
    });

    expect(setMutedVal).toBe(true);
    expect(screen.getByTestId('icon-mute')).toBeInTheDocument();

    const slider = screen.getByTestId('volume-slider');
    act(() => {
      fireEvent.change(slider, { target: { value: '0.5' } });
    });

    expect(setVolumeVal).toBe(0.5);
    expect(setMutedVal).toBe(false);
    expect(screen.getByTestId('icon-volume')).toBeInTheDocument();
  });

  test('play/pause button updates when video ends', () => {
    render(
      <NetflixStylePlayer
        videoSrc="video.mp4"
        title="Test"
        description="Desc"
      />,
    );

    const playBtn = screen.getByTestId('icon-play').closest('button');
    expect(playBtn).toBeInTheDocument();

    act(() => {
      fireEvent.click(playBtn!);
    });

    expect(screen.getByTestId('icon-pause')).toBeInTheDocument();

    const video = document.querySelector('video') as HTMLVideoElement;

    act(() => {
      fireEvent(video, new Event('ended'));
    });

    expect(screen.getByTestId('icon-play')).toBeInTheDocument();
  });
});
