import { act, fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode, Ref } from 'react';
import { ZoomableImage } from '../ZoomableImage';

const mockZoomIn = jest.fn();
const mockZoomOut = jest.fn();
const mockTransformState = {
  scale: 1,
  positionX: 0,
  positionY: 0,
};
const mockSetTransform = jest.fn(
  (positionX: number, positionY: number, scale: number, _duration?: number) => {
    mockTransformState.positionX = positionX;
    mockTransformState.positionY = positionY;
    mockTransformState.scale = scale;
  },
);
let mockWrapperComponent: HTMLDivElement | null = null;
let mockContentComponent: HTMLDivElement | null = null;
let mockShouldExposeContentComponent = true;

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

jest.mock('react-zoom-pan-pinch', () => {
  const React = require('react');

  const TransformWrapper = React.forwardRef(
    ({ children }: { children: ReactNode }, ref: Ref<unknown>) => {
      React.useImperativeHandle(ref, () => ({
        instance: {
          get wrapperComponent() {
            return mockWrapperComponent;
          },
          get contentComponent() {
            return mockShouldExposeContentComponent
              ? mockContentComponent
              : null;
          },
          transformState: mockTransformState,
        },
        setTransform: mockSetTransform,
        zoomIn: mockZoomIn,
        zoomOut: mockZoomOut,
      }));

      return React.createElement(
        'div',
        { 'data-testid': 'transform-wrapper' },
        children,
      );
    },
  );

  const TransformComponent = ({ children }: { children: ReactNode }) =>
    React.createElement(
      'div',
      {
        'data-testid': 'transform-content',
        ref: (node: HTMLDivElement | null) => {
          mockContentComponent = node;
        },
      },
      children,
    );

  return {
    TransformWrapper,
    TransformComponent,
  };
});

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
        x: 0,
        y: 0,
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

const setupWheelScene = ({
  wrapperSize,
  imageSize,
  imageOffset = { left: 0, top: 0 },
}: {
  wrapperSize: { width: number; height: number };
  imageSize: { width: number; height: number };
  imageOffset?: { left: number; top: number };
}) => {
  const { container } = renderZoomableImage();
  const wheelArea = container.firstElementChild as HTMLElement;
  const transformWrapper = screen.getByTestId('transform-wrapper');
  const transformContent = screen.getByTestId('transform-content');
  const image = screen.getByAltText('test image');

  mockWrapperComponent = transformWrapper as HTMLDivElement;
  mockContentComponent = transformContent as HTMLDivElement;

  mockElementRect(
    wheelArea,
    { ...wrapperSize, left: 0, top: 0 },
    { clientWidth: wrapperSize.width, clientHeight: wrapperSize.height },
  );
  mockElementRect(
    transformWrapper,
    { ...wrapperSize, left: 0, top: 0 },
    { clientWidth: wrapperSize.width, clientHeight: wrapperSize.height },
  );
  mockElementRect(
    image,
    {
      ...imageSize,
      left: imageOffset.left,
      top: imageOffset.top,
    },
    { clientWidth: imageSize.width, clientHeight: imageSize.height },
  );

  return { wheelArea, image };
};

const markSceneInitialized = (wheelArea: HTMLElement) => {
  fireEvent.wheel(wheelArea, {
    deltaY: 0,
    clientX: 0,
    clientY: 0,
  });
  mockSetTransform.mockClear();
};

const expectLatestTransform = (
  expectedX: number,
  expectedY: number,
  expectedScale: number,
) => {
  const lastCall = mockSetTransform.mock.calls.at(-1);

  expect(lastCall).toBeDefined();
  expect(lastCall?.[0]).toBeCloseTo(expectedX);
  expect(lastCall?.[1]).toBeCloseTo(expectedY);
  expect(lastCall?.[2]).toBeCloseTo(expectedScale);
  expect(lastCall?.[3]).toBe(0);
};

describe('ZoomableImage wheel behavior', () => {
  beforeEach(() => {
    mockSetTransform.mockClear();
    mockZoomIn.mockClear();
    mockZoomOut.mockClear();
    // Keep the internal wrapper unavailable by default so tests cover the
    // production fallback path where the wheel area owns scroll handling.
    mockWrapperComponent = null;
    mockContentComponent = null;
    mockShouldExposeContentComponent = true;
    mockTransformState.scale = 1;
    mockTransformState.positionX = 0;
    mockTransformState.positionY = 0;
  });

  test('keeps zoom centered while the image still fits in the viewport', () => {
    const { container } = renderZoomableImage();

    const wheelArea = container.firstElementChild as HTMLElement;
    const image = screen.getByAltText('test image');

    mockElementRect(
      wheelArea,
      { width: 800, height: 600, left: 0, top: 0 },
      { clientWidth: 800, clientHeight: 600 },
    );
    mockElementRect(
      image,
      { width: 200, height: 100, left: 100, top: 100 },
      { clientWidth: 200, clientHeight: 100 },
    );

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 750,
      clientY: 550,
    });

    expectLatestTransform(290, 245, 1.1);
  });

  test('centers and stops at the viewport edge before mouse anchoring begins', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 800, height: 600 },
      imageSize: { width: 760, height: 300 },
    });

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });

    expectLatestTransform(0, 142.10526315789474, 1.0526315789473684);
  });

  test('anchors horizontally after the width has reached the viewport edge', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 800, height: 600 },
      imageSize: { width: 760, height: 300 },
    });

    markSceneInitialized(wheelArea);
    mockTransformState.scale = 1.1;
    mockTransformState.positionX = -18;
    mockTransformState.positionY = 135;

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 750,
      clientY: 300,
    });

    expectLatestTransform(-87.81818181818176, 120, 1.2000000000000002);
  });

  test('anchors vertically after the height has reached the viewport edge', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 800, height: 600 },
      imageSize: { width: 300, height: 560 },
    });

    markSceneInitialized(wheelArea);
    mockTransformState.scale = 1.1;
    mockTransformState.positionX = 235;
    mockTransformState.positionY = -8;

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 300,
      clientY: 550,
    });

    expectLatestTransform(220, -58.72727272727275, 1.2000000000000002);
  });

  test('anchors both axes when width and height overflow', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 800, height: 600 },
      imageSize: { width: 900, height: 700 },
    });

    markSceneInitialized(wheelArea);
    mockTransformState.scale = 1;
    mockTransformState.positionX = -50;
    mockTransformState.positionY = -40;

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 700,
      clientY: 500,
    });

    expectLatestTransform(-125, -94, 1.1);
  });

  test('recenters the image when zooming back to minimum scale', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 800, height: 600 },
      imageSize: { width: 400, height: 300 },
    });

    markSceneInitialized(wheelArea);
    mockTransformState.scale = 1.05;
    mockTransformState.positionX = -200;
    mockTransformState.positionY = -150;

    fireEvent.wheel(wheelArea, {
      deltaY: 100,
      clientX: 700,
      clientY: 500,
    });

    expectLatestTransform(200, 150, 1);
  });

  test('uses a fit-to-view minimum scale when the image is larger than the measured viewer', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 500, height: 400 },
      imageSize: { width: 1000, height: 800 },
    });

    markSceneInitialized(wheelArea);
    mockTransformState.scale = 0.55;
    mockTransformState.positionX = -80;
    mockTransformState.positionY = -60;

    fireEvent.wheel(wheelArea, {
      deltaY: 100,
      clientX: 450,
      clientY: 350,
    });

    expectLatestTransform(0, 0, 0.5);
  });

  test('starts a production first wheel from fit-to-view when transform state is stale', () => {
    mockTransformState.scale = 1;
    mockTransformState.positionX = 0;
    mockTransformState.positionY = 0;

    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 500, height: 400 },
      imageSize: { width: 1000, height: 800 },
    });

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 450,
      clientY: 350,
    });

    expectLatestTransform(-90, -70, 0.6);
  });

  test('retries initial fit until the transform content is ready', () => {
    jest.useFakeTimers();
    mockShouldExposeContentComponent = false;

    const { container } = renderZoomableImage();

    const wheelArea = container.firstElementChild as HTMLElement;
    const transformWrapper = screen.getByTestId('transform-wrapper');
    const transformContent = screen.getByTestId('transform-content');
    const image = screen.getByAltText('test image');

    mockWrapperComponent = transformWrapper as HTMLDivElement;
    mockElementRect(
      wheelArea,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockElementRect(
      transformWrapper,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockElementRect(
      image,
      { width: 1000, height: 800, left: 0, top: 0 },
      { clientWidth: 1000, clientHeight: 800 },
    );

    fireEvent.load(image);

    act(() => {
      jest.runOnlyPendingTimers();
    });
    expect(mockSetTransform).not.toHaveBeenCalled();

    mockShouldExposeContentComponent = true;
    mockContentComponent = transformContent as HTMLDivElement;

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expectLatestTransform(0, 0, 0.5);
    jest.useRealTimers();
  });

  test('starts from the new image fit transform after switching images', () => {
    const { container, rerender } = renderZoomableImage({
      imagePath: '/tmp/photo-a.jpg',
    });

    const wheelArea = container.firstElementChild as HTMLElement;
    let transformWrapper = screen.getByTestId('transform-wrapper');
    let image = screen.getByAltText('test image');

    mockWrapperComponent = transformWrapper as HTMLDivElement;
    mockElementRect(
      wheelArea,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockElementRect(
      transformWrapper,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockElementRect(
      image,
      { width: 1000, height: 800, left: 0, top: 0 },
      { clientWidth: 1000, clientHeight: 800 },
    );

    mockTransformState.scale = 2;
    mockTransformState.positionX = -300;
    mockTransformState.positionY = -250;

    rerender(
      <ZoomableImage
        imagePath="/tmp/photo-b.jpg"
        alt="test image"
        rotation={0}
      />,
    );

    transformWrapper = screen.getByTestId('transform-wrapper');
    image = screen.getByAltText('test image');
    mockWrapperComponent = transformWrapper as HTMLDivElement;
    mockElementRect(
      transformWrapper,
      { width: 500, height: 400, left: 0, top: 0 },
      { clientWidth: 500, clientHeight: 400 },
    );
    mockElementRect(
      image,
      { width: 1000, height: 800, left: 0, top: 0 },
      { clientWidth: 1000, clientHeight: 800 },
    );

    fireEvent.load(image);
    mockSetTransform.mockClear();

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 450,
      clientY: 350,
    });

    expectLatestTransform(-90, -70, 0.6);
  });

  test('clamps wheel zoom targets so the image cannot be pulled offscreen', () => {
    const { wheelArea } = setupWheelScene({
      wrapperSize: { width: 800, height: 600 },
      imageSize: { width: 1000, height: 800 },
    });

    markSceneInitialized(wheelArea);
    mockTransformState.scale = 2;
    mockTransformState.positionX = 2000;
    mockTransformState.positionY = 2000;

    fireEvent.wheel(wheelArea, {
      deltaY: -100,
      clientX: 790,
      clientY: 590,
    });

    expectLatestTransform(0, 0, 2.1);
  });
});
