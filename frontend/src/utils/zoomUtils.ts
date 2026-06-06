// Browser line-mode wheel events report lines, not pixels. This normalizes one
// line-scroll notch to the commonly used 33px pixel delta.
export const LINE_HEIGHT_MULTIPLIER = 33;
// Sensitivity for exponential wheel zoom: ratio = exp(normalizedDelta * sensitivity).
// A mouse notch (~100px delta) becomes ~10.5% scale change; trackpad stays smooth.
export const WHEEL_ZOOM_SENSITIVITY = 0.001;
export const MAX_SCALE = 8;
export const MIN_SCALE = 1;
export const SCALE_EPSILON = 0.0001;
export const MAX_FIT_RETRY_FRAMES = 12;
// Multiplicative zoom ratio for the zoom-in/out buttons (50% per click).
export const CONTROL_BUTTON_ZOOM_RATIO = 1.5;

export type Size = {
  width: number;
  height: number;
};

export type OverflowState = {
  width: boolean;
  height: boolean;
};

export type TransformState = {
  positionX: number;
  positionY: number;
  scale: number;
};

export type Geometry = {
  viewportWidth: number;
  viewportHeight: number;
  viewportLeft: number;
  viewportTop: number;
  rawDimensions: Size;
  baseDimensions: Size;
  minScale: number;
};

type ComputeZoomTransformOptions = {
  geometry: Geometry;
  currentTransform: TransformState;
  zoomRatio: number;
  clientX?: number;
  clientY?: number;
};

export const getCenteredAxisPosition = (
  viewportSize: number,
  scaledSize: number,
) => (viewportSize - scaledSize) / 2;

export const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

export const clampOverflowAxisPosition = (
  position: number,
  viewportSize: number,
  scaledSize: number,
) => {
  const minPosition = viewportSize - scaledSize;
  const maxPosition = 0;

  return clamp(position, minPosition, maxPosition);
};

export const getAxisPosition = (
  anchoredPosition: number,
  viewportSize: number,
  scaledSize: number,
  isOverflowingAxis: boolean,
) => {
  const centeredPosition = getCenteredAxisPosition(viewportSize, scaledSize);

  return isOverflowingAxis
    ? clampOverflowAxisPosition(anchoredPosition, viewportSize, scaledSize)
    : centeredPosition;
};

export const getOverflowRatio = (viewportSize: number, scaledSize: number) => {
  if (!viewportSize || scaledSize <= viewportSize) return 0;

  return clamp((scaledSize - viewportSize) / viewportSize, 0, 1);
};

export const interpolate = (from: number, to: number, ratio: number) =>
  from + (to - from) * ratio;

export const getSmoothedWheelAxisPosition = ({
  anchoredPosition,
  viewportSize,
  scaledSize,
  isOverflowingAxis,
  shouldAnchor,
  isZoomingOut,
}: {
  anchoredPosition: number;
  viewportSize: number;
  scaledSize: number;
  isOverflowingAxis: boolean;
  shouldAnchor: boolean;
  isZoomingOut: boolean;
}) => {
  const centeredPosition = getCenteredAxisPosition(viewportSize, scaledSize);

  if (!isOverflowingAxis || !shouldAnchor) return centeredPosition;

  const clampedAnchor = clampOverflowAxisPosition(
    anchoredPosition,
    viewportSize,
    scaledSize,
  );

  if (!isZoomingOut) return clampedAnchor;

  const anchorRatio = getOverflowRatio(viewportSize, scaledSize);

  return interpolate(centeredPosition, clampedAnchor, anchorRatio);
};

export const axisTouchesViewport = (scaledSize: number, viewportSize: number) =>
  scaledSize >= viewportSize - SCALE_EPSILON;

export const getEffectiveDimensions = (
  width: number,
  height: number,
  rotation: number,
): Size => {
  const normalizedRotation = ((rotation % 360) + 360) % 360;
  const isRotated90or270 =
    normalizedRotation === 90 || normalizedRotation === 270;

  return isRotated90or270
    ? { width: height, height: width }
    : { width, height };
};

export const getMinimumScale = (
  baseDimensions: Size,
  viewportWidth: number,
  viewportHeight: number,
) => {
  if (
    !baseDimensions.width ||
    !baseDimensions.height ||
    !viewportWidth ||
    !viewportHeight
  ) {
    return MIN_SCALE;
  }

  return Math.min(
    MIN_SCALE,
    viewportWidth / baseDimensions.width,
    viewportHeight / baseDimensions.height,
  );
};

export const getNextViewportEdgeScale = (
  baseDimensions: Size,
  viewportWidth: number,
  viewportHeight: number,
  currentTouchesViewport: OverflowState,
) => {
  const edgeScales = [];

  if (!currentTouchesViewport.width) {
    edgeScales.push(viewportWidth / baseDimensions.width);
  }

  if (!currentTouchesViewport.height) {
    edgeScales.push(viewportHeight / baseDimensions.height);
  }

  if (!edgeScales.length) return null;

  return Math.min(
    MAX_SCALE,
    Math.max(
      getMinimumScale(baseDimensions, viewportWidth, viewportHeight),
      Math.min(...edgeScales),
    ),
  );
};

export const getScaledDimensions = (
  baseDimensions: Size,
  scale: number,
): Size => ({
  width: baseDimensions.width * scale,
  height: baseDimensions.height * scale,
});

export const getOverflowState = (
  baseDimensions: Size,
  scale: number,
  viewportWidth: number,
  viewportHeight: number,
): OverflowState => {
  const scaledDimensions = getScaledDimensions(baseDimensions, scale);

  return {
    width: scaledDimensions.width > viewportWidth,
    height: scaledDimensions.height > viewportHeight,
  };
};

export const getFitTransform = ({
  baseDimensions,
  viewportWidth,
  viewportHeight,
  minScale,
}: Geometry): TransformState => {
  const scaledDimensions = getScaledDimensions(baseDimensions, minScale);

  return {
    positionX: getCenteredAxisPosition(viewportWidth, scaledDimensions.width),
    positionY: getCenteredAxisPosition(viewportHeight, scaledDimensions.height),
    scale: minScale,
  };
};

export const getElementSize = (element: HTMLElement) => {
  const rect = element.getBoundingClientRect();

  return {
    width: rect.width || element.clientWidth,
    height: rect.height || element.clientHeight,
    left: rect.left,
    top: rect.top,
  };
};

export const computeZoomTransform = ({
  geometry,
  currentTransform,
  zoomRatio,
  clientX,
  clientY,
}: ComputeZoomTransformOptions): TransformState => {
  const desiredScale = clamp(
    currentTransform.scale * zoomRatio,
    geometry.minScale,
    MAX_SCALE,
  );
  const currentDimensions = getScaledDimensions(
    geometry.baseDimensions,
    currentTransform.scale,
  );
  const currentTouchesViewport = {
    width: axisTouchesViewport(currentDimensions.width, geometry.viewportWidth),
    height: axisTouchesViewport(
      currentDimensions.height,
      geometry.viewportHeight,
    ),
  };
  const isZoomingIn = desiredScale > currentTransform.scale;
  const nextViewportEdgeScale = getNextViewportEdgeScale(
    geometry.baseDimensions,
    geometry.viewportWidth,
    geometry.viewportHeight,
    currentTouchesViewport,
  );
  const scale =
    isZoomingIn &&
    nextViewportEdgeScale !== null &&
    desiredScale > nextViewportEdgeScale
      ? nextViewportEdgeScale
      : desiredScale;
  const scaledDimensions = getScaledDimensions(geometry.baseDimensions, scale);
  const newOverflow = getOverflowState(
    geometry.baseDimensions,
    scale,
    geometry.viewportWidth,
    geometry.viewportHeight,
  );
  const mouseViewportX =
    clientX === undefined
      ? geometry.viewportWidth / 2
      : clientX - geometry.viewportLeft;
  const mouseViewportY =
    clientY === undefined
      ? geometry.viewportHeight / 2
      : clientY - geometry.viewportTop;
  const isWithinViewport =
    mouseViewportX >= 0 &&
    mouseViewportX <= geometry.viewportWidth &&
    mouseViewportY >= 0 &&
    mouseViewportY <= geometry.viewportHeight;
  const ratio = currentTransform.scale > 0 ? scale / currentTransform.scale : 1;
  const anchoredX =
    mouseViewportX - (mouseViewportX - currentTransform.positionX) * ratio;
  const anchoredY =
    mouseViewportY - (mouseViewportY - currentTransform.positionY) * ratio;
  const isZoomingOut = scale < currentTransform.scale;

  return {
    positionX: getSmoothedWheelAxisPosition({
      anchoredPosition: anchoredX,
      viewportSize: geometry.viewportWidth,
      scaledSize: scaledDimensions.width,
      isOverflowingAxis: newOverflow.width,
      shouldAnchor:
        isWithinViewport && currentTouchesViewport.width && newOverflow.width,
      isZoomingOut,
    }),
    positionY: getSmoothedWheelAxisPosition({
      anchoredPosition: anchoredY,
      viewportSize: geometry.viewportHeight,
      scaledSize: scaledDimensions.height,
      isOverflowingAxis: newOverflow.height,
      shouldAnchor:
        isWithinViewport && currentTouchesViewport.height && newOverflow.height,
      isZoomingOut,
    }),
    scale,
  };
};
