import { render, screen, fireEvent, act } from '@testing-library/react';
import fs from 'fs';
import path from 'path';
import NetflixStylePlayer from '../NetflixStylePlayer';

// Mock Tauri convertFileSrc API
jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

// Mock Slider component to use simple range input for testing
jest.mock('../../ui/Slider', () => ({
  Slider: ({
    onValueChange,
    value = [0],
    min,
    max,
    step,
  }: {
    onValueChange?: (value: number[]) => void;
    value?: number[];
    min?: number;
    max?: number;
    step?: number;
  }) => (
    <input
      data-testid="volume-slider"
      type="range"
      min={min}
      max={max}
      step={step}
      value={value[0]}
      onChange={(e) => onValueChange?.([Number.parseFloat(e.target.value)])}
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

const mockVideoProperties = (video: HTMLVideoElement) => {
  const state = {
    muted: false,
    volume: 1,
    currentTime: 0,
  };

  Object.defineProperty(video, 'muted', {
    get: () => state.muted,
    set: (val) => {
      state.muted = val;
    },
    configurable: true,
  });

  Object.defineProperty(video, 'volume', {
    get: () => state.volume,
    set: (val) => {
      state.volume = val;
    },
    configurable: true,
  });

  Object.defineProperty(video, 'currentTime', {
    get: () => state.currentTime,
    set: (val) => {
      state.currentTime = val;
    },
    configurable: true,
  });

  return state;
};

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

    const videoMockState = mockVideoProperties(video);

    const muteBtn = screen.getByTestId('icon-volume').closest('button');
    expect(muteBtn).toBeInTheDocument();

    act(() => {
      fireEvent.click(muteBtn!);
    });

    expect(videoMockState.muted).toBe(true);
    expect(screen.getByTestId('icon-mute')).toBeInTheDocument();

    const slider = screen.getByTestId('volume-slider');
    act(() => {
      fireEvent.change(slider, { target: { value: '0.5' } });
    });

    expect(videoMockState.volume).toBe(0.5);
    expect(videoMockState.muted).toBe(false);
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

  test('handles keyboard shortcuts for play/pause, seek, mute, and fullscreen', () => {
    render(
      <NetflixStylePlayer
        videoSrc="video.mp4"
        title="Test"
        description="Desc"
      />,
    );

    const video = document.querySelector('video') as HTMLVideoElement;

    const videoMockState = mockVideoProperties(video);
    Object.defineProperty(video, 'duration', {
      value: 120,
      writable: true,
      configurable: true,
    });

    expect(screen.getByTestId('icon-play')).toBeInTheDocument();
    act(() => {
      fireEvent.keyDown(document, { key: ' ' });
    });
    expect(screen.getByTestId('icon-pause')).toBeInTheDocument();

    expect(screen.queryByTestId('icon-mute')).not.toBeInTheDocument();
    act(() => {
      fireEvent.keyDown(document, { key: 'm' });
    });
    expect(videoMockState.muted).toBe(true);
    expect(screen.getByTestId('icon-mute')).toBeInTheDocument();

    expect(videoMockState.currentTime).toBe(0);
    act(() => {
      fireEvent.keyDown(document, { key: 'ArrowRight' });
    });
    expect(videoMockState.currentTime).toBe(10);

    act(() => {
      fireEvent.keyDown(document, { key: 'ArrowLeft' });
    });
    expect(videoMockState.currentTime).toBe(0);

    expect(requestFullscreenMock).not.toHaveBeenCalled();
    act(() => {
      fireEvent.keyDown(document, { key: 'f' });
    });
    expect(requestFullscreenMock).toHaveBeenCalled();

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    try {
      act(() => {
        fireEvent.keyDown(input, { key: ' ' });
      });
      expect(screen.getByTestId('icon-pause')).toBeInTheDocument();
    } finally {
      document.body.removeChild(input);
    }
  });

  test('renders title and description overlay', () => {
    render(
      <NetflixStylePlayer
        videoSrc="video.mp4"
        title="My Great Video"
        description="A description of the video"
      />,
    );

    expect(screen.getByText('My Great Video')).toBeInTheDocument();
    expect(screen.getByText('A description of the video')).toBeInTheDocument();
  });

  test('exposes the progress bar as an accessible slider', () => {
    render(
      <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
    );

    const seekBar = screen.getByRole('slider', { name: 'Seek' });
    expect(seekBar).toHaveAttribute('aria-valuemin', '0');
    expect(seekBar).toHaveAttribute('tabindex', '0');

    const video = document.querySelector('video') as HTMLVideoElement;
    const videoMockState = mockVideoProperties(video);
    Object.defineProperty(video, 'duration', {
      value: 100,
      writable: true,
      configurable: true,
    });

    act(() => {
      seekBar.focus();
      fireEvent.keyDown(seekBar, { key: 'ArrowRight' });
    });
    expect(videoMockState.currentTime).toBe(5);

    act(() => {
      fireEvent.keyDown(seekBar, { key: 'End' });
    });
    expect(videoMockState.currentTime).toBe(100);

    act(() => {
      fireEvent.keyDown(seekBar, { key: 'Home' });
    });
    expect(videoMockState.currentTime).toBe(0);
  });

  test('control buttons have descriptive, state-aware aria-labels', () => {
    render(
      <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
    );

    expect(
      screen.getByRole('button', { name: 'Rewind 10 seconds' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Fast forward 10 seconds' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Mute' })).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Enter fullscreen' }),
    ).toBeInTheDocument();

    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Play' }));
    });
    expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument();
  });

  test('controls are visible by default while paused and hide only while playing', () => {
    const { container } = render(
      <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
    );

    const controls = container.querySelector(
      '.absolute.right-0.bottom-4',
    ) as HTMLElement;
    expect(controls.className).toContain('opacity-100');
    expect(controls.className).toContain('pointer-events-auto');

    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Play' }));
    });
    expect(controls.className).toContain('opacity-0');
    expect(controls.className).toContain('pointer-events-none');

    const player = container.firstChild as HTMLElement;
    act(() => {
      fireEvent.mouseEnter(player);
    });
    expect(controls.className).toContain('opacity-100');

    act(() => {
      fireEvent.mouseLeave(player);
    });
    expect(controls.className).toContain('opacity-0');
  });

  describe('Tauri CSP Policy Configuration', () => {
    test('tauri.conf.json whitelists asset: and http://asset.localhost in media-src CSP', () => {
      const configPath = path.resolve(
        __dirname,
        '../../../../src-tauri/tauri.conf.json',
      );
      const configRaw = fs.readFileSync(configPath, 'utf8');
      const config = JSON.parse(configRaw);

      const csp = config.app?.security?.csp;
      expect(csp).toBeDefined();

      const mediaSrcMatch = csp.match(/media-src\s+([^;]+)/);
      expect(mediaSrcMatch).toBeTruthy();

      const mediaSrcDirective = mediaSrcMatch[1];
      expect(mediaSrcDirective).toContain('asset:');
      expect(mediaSrcDirective).toContain('http://asset.localhost');
    });
  });
});
