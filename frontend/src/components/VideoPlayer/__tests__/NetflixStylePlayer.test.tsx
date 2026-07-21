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
    'aria-label': ariaLabel,
  }: {
    onValueChange?: (value: number[]) => void;
    value?: number[];
    min?: number;
    max?: number;
    step?: number;
    'aria-label'?: string;
  }) => (
    <input
      data-testid="volume-slider"
      type="range"
      min={min}
      max={max}
      step={step}
      value={value[0]}
      aria-label={ariaLabel}
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
    expect(screen.getByRole('slider', { name: 'Volume' })).toBeInTheDocument();

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

  test('controls remain visible while keyboard focus is inside the player', () => {
    jest.useFakeTimers();
    try {
      const { container } = render(
        <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
      );
      const controls = container.querySelector(
        '.absolute.right-0.bottom-4',
      ) as HTMLElement;

      // Start playback so controls would otherwise auto-hide.
      act(() => {
        fireEvent.click(screen.getByRole('button', { name: 'Play' }));
      });
      expect(controls.className).toContain('opacity-0');

      // Focusing a control reveals the controls...
      act(() => {
        screen.getByRole('button', { name: 'Pause' }).focus();
      });
      expect(controls.className).toContain('opacity-100');

      // ...and they stay visible past the auto-hide delay while focused.
      act(() => {
        jest.advanceTimersByTime(4000);
      });
      expect(controls.className).toContain('opacity-100');

      // Once focus leaves the player, controls hide again.
      act(() => {
        (document.activeElement as HTMLElement)?.blur();
      });
      expect(controls.className).toContain('opacity-0');
    } finally {
      jest.useRealTimers();
    }
  });

  test('shows an error message when the video fails to decode', () => {
    render(
      <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
    );

    expect(
      screen.queryByText('This video cannot be played'),
    ).not.toBeInTheDocument();

    const video = document.querySelector('video') as HTMLVideoElement;
    act(() => {
      fireEvent(video, new Event('error'));
    });

    expect(screen.getByText('This video cannot be played')).toBeInTheDocument();
  });

  test('does not autoplay by default', () => {
    jest.useFakeTimers();
    try {
      render(
        <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
      );
      act(() => {
        jest.advanceTimersByTime(1000);
      });
      expect(window.HTMLMediaElement.prototype.play).not.toHaveBeenCalled();
      expect(screen.getByTestId('icon-play')).toBeInTheDocument();
    } finally {
      jest.useRealTimers();
    }
  });

  test('autoplays after a short delay when autoPlay is set', () => {
    jest.useFakeTimers();
    try {
      render(
        <NetflixStylePlayer
          videoSrc="video.mp4"
          title="Test"
          description=""
          autoPlay
        />,
      );

      // Nothing happens immediately — the delay hasn't elapsed yet.
      expect(window.HTMLMediaElement.prototype.play).not.toHaveBeenCalled();
      expect(screen.getByTestId('icon-play')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(500);
      });

      expect(window.HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId('icon-pause')).toBeInTheDocument();
    } finally {
      jest.useRealTimers();
    }
  });

  describe('seek bar hover preview', () => {
    /** Renders the player with a known duration and a measurable seek bar. */
    const setupSeekBar = (duration = 100, width = 400) => {
      render(
        <NetflixStylePlayer videoSrc="video.mp4" title="Test" description="" />,
      );
      const video = document.querySelector('video') as HTMLVideoElement;
      Object.defineProperty(video, 'duration', {
        value: duration,
        writable: true,
        configurable: true,
      });

      const seekBar = screen.getByRole('slider', { name: 'Seek' });
      seekBar.getBoundingClientRect = jest.fn(
        () => ({ left: 0, width, top: 0, height: 1 }) as DOMRect,
      );
      // The padded wrapper carries the pointer handlers.
      return { hitArea: seekBar.parentElement as HTMLElement };
    };

    test('is not mounted until the user first hovers the bar', () => {
      const { hitArea } = setupSeekBar();
      expect(screen.queryByTestId('seek-preview')).not.toBeInTheDocument();

      act(() => {
        fireEvent.mouseEnter(hitArea, { clientX: 200 });
      });
      expect(screen.getByTestId('seek-preview')).toBeInTheDocument();
    });

    test('shows the timestamp for the hovered position', () => {
      const { hitArea } = setupSeekBar(100, 400);

      act(() => {
        fireEvent.mouseEnter(hitArea, { clientX: 200 });
      });
      // Halfway across a 100s video
      expect(screen.getByTestId('seek-preview')).toHaveTextContent('0:50');

      act(() => {
        fireEvent.mouseMove(hitArea, { clientX: 100 });
      });
      expect(screen.getByTestId('seek-preview')).toHaveTextContent('0:25');
    });

    test('seeks the hidden preview video to the hovered time', () => {
      const { hitArea } = setupSeekBar(100, 400);

      act(() => {
        fireEvent.mouseEnter(hitArea, { clientX: 200 });
      });

      const preview = document.querySelector(
        '[data-testid="seek-preview"] video',
      ) as HTMLVideoElement;
      expect(preview).toBeInTheDocument();

      // jsdom doesn't implement media seeking, so observe currentTime directly.
      const previewState = mockVideoProperties(preview);

      act(() => {
        fireEvent.mouseMove(hitArea, { clientX: 100 });
      });
      expect(previewState.currentTime).toBeCloseTo(25);

      act(() => {
        fireEvent.mouseMove(hitArea, { clientX: 300 });
      });
      expect(previewState.currentTime).toBeCloseTo(75);
    });

    test('keeps the preview inside the bar at the edges', () => {
      const { hitArea } = setupSeekBar(100, 400);

      act(() => {
        fireEvent.mouseEnter(hitArea, { clientX: 0 });
      });
      // Clamped to half the preview width rather than sitting at 0
      expect(screen.getByTestId('seek-preview')).toHaveStyle({ left: '80px' });

      act(() => {
        fireEvent.mouseMove(hitArea, { clientX: 400 });
      });
      expect(screen.getByTestId('seek-preview')).toHaveStyle({ left: '320px' });
    });

    test('hides the preview when the pointer leaves the bar', () => {
      const { hitArea } = setupSeekBar();

      act(() => {
        fireEvent.mouseEnter(hitArea, { clientX: 200 });
      });
      expect(screen.getByTestId('seek-preview')).toHaveClass('opacity-100');

      act(() => {
        fireEvent.mouseLeave(hitArea);
      });
      // Stays mounted (so later hovers are instant) but is hidden
      expect(screen.getByTestId('seek-preview')).toHaveClass('opacity-0');
    });
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
