import { act, fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { ZoomableImage, ZoomableImageRef } from '../ZoomableImage';
import { MAX_FIT_RETRY_FRAMES } from '@/utils/zoomUtils';

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

class ResizeObserverMock {
  observe = jest.fn();
  disconnect = jest.fn();
}

const mockElementRect = (
  element: Element,
  rect: Partial<DOMRect>,
  dimensions?: { clientWidth?: number; clientHeight?: number },
) => {
  Object.defineProperty(element, 'getBoundingClientRect', {
    configurable: true,
    value: () =>
      ({
        left: 0,
        top: 0,
        right: (rect.left ?? 0) + (rect.width ?? 0),
        bottom: (rect.top ?? 0) + (rect.height ?? 0),
        x: rect.left ?? 0,
        y: rect.top ?? 0,
        width: 0,
        height: 0,
        toJSON: () => undefined,
        ...rect,
      }) as DOMRect,
  });

  if (dimensions?.clientWidth !== undefined) {
    Object.defineProperty(element, 'clientWidth', {
      configurable: true,
      value: dimensions.clientWidth,
    });
  }

  if (dimensions?.clientHeight !== undefined) {
    Object.defineProperty(element, 'clientHeight', {
      configurable: true,
      value: dimensions.clientHeight,
    });
  }
};

const mockImageDimensions = (
  image: HTMLElement,
  dimensions: { width: number; height: number; complete?: boolean },
) => {
  Object.defineProperty(image, 'naturalWidth', {
    configurable: true,
    value: dimensions.width,
  });
  Object.defineProperty(image, 'naturalHeight', {
    configurable: true,
    value: dimensions.height,
  });
  Object.defineProperty(image, 'clientWidth', {
    configurable: true,
    value: dimensions.width,
  });
  Object.defineProperty(image, 'clientHeight', {
    configurable: true,
    value: dimensions.height,
  });
  Object.defineProperty(image, 'complete', {
    configurable: true,
    value: dimensions.complete ?? true,
  });
};

const renderZoomableImage = (
  props: Partial<{
    imagePath: string;
    alt: string;
    rotation: number;
    resetSignal: number;
  }> = {},
) =>
  render(
    <ZoomableImage
      imagePath="/tmp/photo.jpg"
      alt="test image"
      rotation={0}
      {...props}
    />,
  );

const setupScene = ({
  viewportSize,
  imageSize,
  props,
}: {
  viewportSize: { width: number; height: number };
  imageSize: { width: number; height: number };
  props?: Partial<{
    imagePath: string;
    alt: string;
    rotation: number;
    resetSignal: number;
  }>;
}) => {
  const renderResult = renderZoomableImage(props);
  const viewport = screen.getByTestId('zoom-viewport');
  const content = screen.getByTestId('zoom-content');
  const image = screen.getByAltText('test image');

  mockElementRect(
    viewport,
    { ...viewportSize, left: 0, top: 0 },
    { clientWidth: viewportSize.width, clientHeight: viewportSize.height },
  );
  mockImageDimensions(image, imageSize);

  fireEvent.load(image);

  return { ...renderResult, viewport, content, image };
};

const getCurrentTransform = () => {
  const content = screen.getByTestId('zoom-content');
  const transform = content.style.transform;
  const match = transform.match(
    /translate3d\((-?[\d.]+)px, (-?[\d.]+)px, 0\) scale\((-?[\d.]+)\)/,
  );

  if (!match) {
    throw new Error(`Unexpected transform: ${transform}`);
  }

  return {
    positionX: Number(match[1]),
    positionY: Number(match[2]),
    scale: Number(match[3]),
  };
};

const expectCurrentTransform = (
  expectedX: number,
  expectedY: number,
  expectedScale: number,
) => {
  const transform = getCurrentTransform();

  expect(transform.positionX).toBeCloseTo(expectedX);
  expect(transform.positionY).toBeCloseTo(expectedY);
  expect(transform.scale).toBeCloseTo(expectedScale);
};

const firePointerEvent = (
  element: Element,
  type: string,
  properties: Record<string, number | string> = {},
) => {
  const event = new Event(type, { bubbles: true, cancelable: true });

  Object.entries(properties).forEach(([key, value]) => {
    Object.defineProperty(event, key, {
      configurable: true,
      value,
    });
  });

  fireEvent(element, event);
};

const installPointerCaptureMocks = (element: Element) => {
  const capturedPointers = new Set<number>();

  Object.defineProperty(element, 'setPointerCapture', {
    configurable: true,
    value: jest.fn((pointerId: number) => {
      capturedPointers.add(pointerId);
    }),
  });
  Object.defineProperty(element, 'releasePointerCapture', {
    configurable: true,
    value: jest.fn((pointerId: number) => {
      capturedPointers.delete(pointerId);
    }),
  });
  Object.defineProperty(element, 'hasPointerCapture', {
    configurable: true,
    value: jest.fn((pointerId: number) => capturedPointers.has(pointerId)),
  });
};

const zoomToOverflow = (viewport: Element) => {
  fireEvent.wheel(viewport, {
    deltaY: -100,
    clientX: 700,
    clientY: 500,
  });
};

const startPan = (viewport: Element, pointerId = 5) => {
  firePointerEvent(viewport, 'pointerdown', {
    button: 0,
    buttons: 1,
    pointerId,
    clientX: 300,
    clientY: 300,
  });
};

type ManualAnimationFrames = {
  frames: Map<number, FrameRequestCallback>;
  flushNextFrame: () => void;
};

// Replaces the synchronous rAF/cAF mocks (installed in beforeEach) with a manual
// queue so a single generation of scheduled fit attempts can be flushed at a
// time. This makes the fit-retry loop deterministic to assert against.
const setupManualAnimationFrames = (): ManualAnimationFrames => {
  const frames = new Map<number, FrameRequestCallback>();
  let nextFrameId = 1;

  (window.requestAnimationFrame as unknown as jest.Mock).mockImplementation(
    (callback: FrameRequestCallback) => {
      const id = nextFrameId;
      nextFrameId += 1;
      frames.set(id, callback);
      return id;
    },
  );
  (window.cancelAnimationFrame as unknown as jest.Mock).mockImplementation(
    (id: number) => {
      frames.delete(id);
    },
  );

  const flushNextFrame = () => {
    const callbacks = Array.from(frames.values());
    frames.clear();
    act(() => {
      callbacks.forEach((callback) => callback(0));
    });
  };

  return { frames, flushNextFrame };
};

describe('ZoomableImage controlled transform behavior', () => {
  beforeEach(() => {
    global.ResizeObserver =
      ResizeObserverMock as unknown as typeof ResizeObserver;
    jest
      .spyOn(window, 'requestAnimationFrame')
      .mockImplementation((callback: FrameRequestCallback) => {
        callback(0);
        return 1;
      });
    jest
      .spyOn(window, 'cancelAnimationFrame')
      .mockImplementation(() => undefined);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('fits a large image to the measured viewport on load', () => {
    setupScene({
      viewportSize: { width: 500, height: 400 },
      imageSize: { width: 1000, height: 800 },
    });

    expectCurrentTransform(0, 0, 0.5);
  });

  test('keeps zoom centered while the image still fits in the viewport', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 200, height: 100 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 750,
      clientY: 550,
    });

    expectCurrentTransform(290, 245, 1.1);
  });

  test('stops at the first viewport edge before mouse anchoring begins', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 760, height: 300 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });

    expectCurrentTransform(0, 142.10526315789474, 1.0526315789473684);
  });

  test('stops a newly overflowing axis at the viewport edge before anchoring it', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 700,
      clientY: 500,
    });

    expectCurrentTransform(0, -18.518518518518476, 0.8888888888888888);
  });

  test('anchors horizontally only after width has reached the viewport edge', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 760, height: 300 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });
    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });

    expectCurrentTransform(-71.25, 127.10526315789474, 1.1526315789473685);
  });

  test('anchors vertically only after height has reached the viewport edge', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 300, height: 560 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 300,
      clientY: 550,
    });
    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 300,
      clientY: 550,
    });

    expectCurrentTransform(
      224.28571428571428,
      -51.33333333333337,
      1.1714285714285715,
    );
  });

  test('anchors both axes when width and height overflow', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 700,
      clientY: 500,
    });
    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 700,
      clientY: 500,
    });

    expectCurrentTransform(-78.75, -76.85185185185185, 0.9888888888888888);
  });

  test('recenters when zooming back to minimum scale', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 400, height: 300 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 700,
      clientY: 500,
    });
    fireEvent.wheel(viewport, {
      deltaY: 100,
      clientX: 700,
      clientY: 500,
    });

    expectCurrentTransform(200, 150, 1);
  });

  test('blends overflowing axes back toward center while zooming out', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 1600, height: 1200 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 700,
      clientY: 500,
    });
    fireEvent.wheel(viewport, {
      deltaY: 50,
      clientX: 700,
      clientY: 500,
    });

    expectCurrentTransform(-43, -32, 0.55);
  });

  test('panning clamps overflowing axes and keeps fitting axes centered', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 760, height: 300 },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });
    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });
    firePointerEvent(viewport, 'pointerdown', {
      button: 0,
      buttons: 1,
      pointerId: 1,
      clientX: 300,
      clientY: 300,
    });
    firePointerEvent(viewport, 'pointermove', {
      pointerId: 1,
      clientX: 1000,
      clientY: 1000,
    });
    firePointerEvent(viewport, 'pointerup', {
      pointerId: 1,
      clientX: 1000,
      clientY: 1000,
    });

    expectCurrentTransform(0, 127.10526315789474, 1.1526315789473685);
  });

  test('reuses the drag-start geometry while panning', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });
    const getBoundingClientRect = jest.fn(
      () =>
        ({
          left: 0,
          top: 0,
          right: 800,
          bottom: 600,
          x: 0,
          y: 0,
          width: 800,
          height: 600,
          toJSON: () => undefined,
        }) as DOMRect,
    );

    Object.defineProperty(viewport, 'getBoundingClientRect', {
      configurable: true,
      value: getBoundingClientRect,
    });

    zoomToOverflow(viewport);
    startPan(viewport, 1);

    const callsAfterDragStart = getBoundingClientRect.mock.calls.length;

    firePointerEvent(viewport, 'pointermove', {
      pointerId: 1,
      clientX: 350,
      clientY: 350,
    });
    firePointerEvent(viewport, 'pointermove', {
      pointerId: 1,
      clientX: 400,
      clientY: 400,
    });

    expect(getBoundingClientRect).toHaveBeenCalledTimes(callsAfterDragStart);
  });

  test('cleans up panning on pointer leave when pointer capture is unavailable', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    zoomToOverflow(viewport);
    startPan(viewport);

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'pointerout', {
      pointerId: 5,
      clientX: 900,
      clientY: 700,
    });

    expect(viewport).not.toHaveStyle({ cursor: 'grabbing' });
  });

  test('keeps panning when the pointer leaves while capture is held', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });
    installPointerCaptureMocks(viewport);

    zoomToOverflow(viewport);
    startPan(viewport);

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'pointerout', {
      pointerId: 5,
      clientX: 900,
      clientY: 700,
    });

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'pointerup', {
      pointerId: 5,
      clientX: 900,
      clientY: 700,
    });

    expect(viewport).not.toHaveStyle({ cursor: 'grabbing' });
  });

  test('cleans up panning on pointer cancel', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    zoomToOverflow(viewport);
    startPan(viewport);

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'pointercancel', {
      pointerId: 5,
      clientX: 300,
      clientY: 300,
    });

    expect(viewport).not.toHaveStyle({ cursor: 'grabbing' });
  });

  test('cleans up panning when pointer capture is lost', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    zoomToOverflow(viewport);
    startPan(viewport);

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'lostpointercapture', {
      pointerId: 5,
      clientX: 300,
      clientY: 300,
    });

    expect(viewport).not.toHaveStyle({ cursor: 'grabbing' });
  });

  test('cleans up panning on pointer up after pointer capture succeeds', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });
    installPointerCaptureMocks(viewport);

    zoomToOverflow(viewport);
    startPan(viewport);

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });
    expect(viewport.setPointerCapture).toHaveBeenCalledWith(5);
    expect(viewport.hasPointerCapture(5)).toBe(true);

    firePointerEvent(viewport, 'pointerup', {
      pointerId: 5,
      clientX: 300,
      clientY: 300,
    });

    expect(viewport.releasePointerCapture).toHaveBeenCalledWith(5);
    expect(viewport.hasPointerCapture(5)).toBe(false);
    expect(viewport).not.toHaveStyle({ cursor: 'grabbing' });
  });

  test('does not replace an active drag with a second pointer', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    zoomToOverflow(viewport);
    startPan(viewport, 1);
    startPan(viewport, 2);

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'pointerup', {
      pointerId: 2,
      clientX: 300,
      clientY: 300,
    });

    expect(viewport).toHaveStyle({ cursor: 'grabbing' });

    firePointerEvent(viewport, 'pointerup', {
      pointerId: 1,
      clientX: 300,
      clientY: 300,
    });

    expect(viewport).not.toHaveStyle({ cursor: 'grabbing' });
  });

  test('does not use client dimensions before the image natural size is ready', () => {
    renderZoomableImage();

    const viewport = screen.getByTestId('zoom-viewport');
    const content = screen.getByTestId('zoom-content');
    const image = screen.getByAltText('test image');

    mockElementRect(
      viewport,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockImageDimensions(image, {
      width: 0,
      height: 0,
      complete: false,
    });
    Object.defineProperty(image, 'clientWidth', {
      configurable: true,
      value: 1000,
    });
    Object.defineProperty(image, 'clientHeight', {
      configurable: true,
      value: 800,
    });

    fireEvent.load(image);

    expect(content.style.width).not.toBe('1000px');
    expect(content.style.height).not.toBe('800px');
    expect(image.style.width).toBe('');
    expect(image.style.height).toBe('');
  });

  test('starts from the new image fit transform after switching images', () => {
    const { viewport, rerender } = setupScene({
      viewportSize: { width: 500, height: 400 },
      imageSize: { width: 1000, height: 800 },
      props: { imagePath: '/tmp/photo-a.jpg' },
    });

    fireEvent.wheel(viewport, {
      deltaY: -100,
      clientX: 450,
      clientY: 350,
    });

    rerender(
      <ZoomableImage
        imagePath="/tmp/photo-b.jpg"
        alt="test image"
        rotation={0}
      />,
    );

    const newImage = screen.getByAltText('test image');
    mockImageDimensions(newImage, { width: 200, height: 100 });
    fireEvent.load(newImage);

    expectCurrentTransform(150, 150, 1);
  });

  test('rotation recalculates the fit transform', () => {
    const { rerender } = setupScene({
      viewportSize: { width: 600, height: 400 },
      imageSize: { width: 1000, height: 500 },
      props: { rotation: 0 },
    });

    expectCurrentTransform(0, 50, 0.6);

    rerender(
      <ZoomableImage
        imagePath="/tmp/photo.jpg"
        alt="test image"
        rotation={90}
      />,
    );

    const image = screen.getByAltText('test image');
    mockImageDimensions(image, { width: 1000, height: 500 });
    fireEvent.load(image);

    expectCurrentTransform(200, 0, 0.4);
  });

  test('imperative reset returns to fit-to-view', () => {
    const imageRef = createRef<ZoomableImageRef>();

    render(
      <ZoomableImage
        ref={imageRef}
        imagePath="/tmp/photo.jpg"
        alt="test image"
        rotation={0}
      />,
    );

    const viewport = screen.getByTestId('zoom-viewport');
    const image = screen.getByAltText('test image');
    mockElementRect(
      viewport,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockImageDimensions(image, { width: 1000, height: 800 });
    fireEvent.load(image);

    act(() => {
      imageRef.current?.zoomIn();
      imageRef.current?.reset();
    });

    expectCurrentTransform(0, 0, 0.5);
  });

  test('applies the line-height multiplier for line-mode wheel events', () => {
    const { viewport } = setupScene({
      viewportSize: { width: 800, height: 600 },
      imageSize: { width: 200, height: 100 },
    });

    // A line-mode wheel (deltaMode === 1) reports scroll in lines, not pixels.
    // It must be normalized by LINE_HEIGHT_MULTIPLIER (33), so a 3-line notch
    // zooms by 3 * 33 * ZOOM_FACTOR(0.001) = 0.099 -> scale 1.099, identical to
    // a 99px pixel-mode notch. Without the multiplier it would be only 0.003.
    fireEvent.wheel(viewport, {
      deltaY: -3,
      deltaMode: 1,
      clientX: 400,
      clientY: 300,
    });

    expectCurrentTransform(290.1, 245.05, 1.099);
  });

  test('retries the fit until the viewport can be measured', () => {
    const { flushNextFrame } = setupManualAnimationFrames();

    renderZoomableImage();
    const viewport = screen.getByTestId('zoom-viewport');
    const image = screen.getByAltText('test image');

    // The image dimensions are known, but the viewport cannot be measured yet.
    mockElementRect(
      viewport,
      { width: 0, height: 0, left: 0, top: 0 },
      { clientWidth: 0, clientHeight: 0 },
    );
    mockImageDimensions(image, { width: 1000, height: 800 });
    fireEvent.load(image);

    // Fit attempts run but cannot succeed while the viewport has no size, so
    // the transform stays at its initial (unfitted) value.
    flushNextFrame();
    flushNextFrame();
    expectCurrentTransform(0, 0, 1);

    // Once the viewport reports a size, the next retry fits the image.
    mockElementRect(
      viewport,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    flushNextFrame();

    expectCurrentTransform(0, 0, 0.5);
  });

  test('stops retrying after the maximum number of frames and recovers on resize', () => {
    const { frames, flushNextFrame } = setupManualAnimationFrames();

    renderZoomableImage();
    const viewport = screen.getByTestId('zoom-viewport');
    const image = screen.getByAltText('test image');

    mockElementRect(
      viewport,
      { width: 0, height: 0, left: 0, top: 0 },
      { clientWidth: 0, clientHeight: 0 },
    );
    mockImageDimensions(image, { width: 1000, height: 800 });
    fireEvent.load(image);

    // Exhaust every retry while the viewport stays unmeasurable.
    for (let i = 0; i < MAX_FIT_RETRY_FRAMES + 2; i += 1) {
      flushNextFrame();
    }

    // The retry loop has given up: nothing is scheduled and no fit happened.
    expect(frames.size).toBe(0);
    expectCurrentTransform(0, 0, 1);

    // A now-measurable viewport alone does not revive the abandoned loop.
    mockElementRect(
      viewport,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    flushNextFrame();
    expectCurrentTransform(0, 0, 1);

    // A fresh fit cycle (resize) resets the retry count and fits the image.
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    flushNextFrame();

    expectCurrentTransform(0, 0, 0.5);
  });
});
