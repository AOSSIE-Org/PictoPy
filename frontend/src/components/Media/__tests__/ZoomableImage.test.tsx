import { act, fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { ZoomableImage, ZoomableImageRef } from '../ZoomableImage';

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
  dimensions: { width: number; height: number },
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
    fireEvent.mouseDown(viewport, {
      button: 0,
      clientX: 300,
      clientY: 300,
    });
    fireEvent.mouseMove(viewport, {
      clientX: 1000,
      clientY: 1000,
    });
    fireEvent.mouseUp(viewport, {
      clientX: 1000,
      clientY: 1000,
    });

    expectCurrentTransform(0, 127.10526315789474, 1.1526315789473685);
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
});
