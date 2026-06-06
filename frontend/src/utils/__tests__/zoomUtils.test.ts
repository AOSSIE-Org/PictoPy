import {
  computeZoomTransform,
  getFitTransform,
  getMinimumScale,
  type Geometry,
} from '../zoomUtils';

const makeGeometry = (overrides: Partial<Geometry> = {}): Geometry => {
  const baseDimensions = overrides.baseDimensions ?? {
    width: 800,
    height: 600,
  };
  const viewportWidth = overrides.viewportWidth ?? 800;
  const viewportHeight = overrides.viewportHeight ?? 600;

  return {
    viewportWidth,
    viewportHeight,
    viewportLeft: 0,
    viewportTop: 0,
    rawDimensions: baseDimensions,
    baseDimensions,
    minScale: getMinimumScale(baseDimensions, viewportWidth, viewportHeight),
    ...overrides,
  };
};

describe('zoomUtils', () => {
  test('computes fit scale and centered transform for a large image', () => {
    const geometry = makeGeometry({
      viewportWidth: 500,
      viewportHeight: 400,
      baseDimensions: { width: 1000, height: 800 },
      rawDimensions: { width: 1000, height: 800 },
      minScale: 0.5,
    });

    expect(getFitTransform(geometry)).toEqual({
      positionX: 0,
      positionY: 0,
      scale: 0.5,
    });
  });

  test('keeps zoom centered while the image still fits', () => {
    const geometry = makeGeometry({
      viewportWidth: 800,
      viewportHeight: 600,
      viewportLeft: 20,
      viewportTop: 10,
      baseDimensions: { width: 200, height: 100 },
      rawDimensions: { width: 200, height: 100 },
      minScale: 1,
    });

    const next = computeZoomTransform({
      geometry,
      currentTransform: { positionX: 300, positionY: 250, scale: 1 },
      zoomRatio: 1.1,
      clientX: 770,
      clientY: 560,
    });

    expect(next.positionX).toBeCloseTo(290);
    expect(next.positionY).toBeCloseTo(245);
    expect(next.scale).toBeCloseTo(1.1);
  });

  test('stops at the first viewport edge before mouse anchoring begins', () => {
    const geometry = makeGeometry({
      viewportWidth: 800,
      viewportHeight: 600,
      baseDimensions: { width: 760, height: 300 },
      rawDimensions: { width: 760, height: 300 },
      minScale: 1,
    });

    const next = computeZoomTransform({
      geometry,
      currentTransform: { positionX: 20, positionY: 150, scale: 1 },
      zoomRatio: 1.1,
      clientX: 750,
      clientY: 300,
    });

    expect(next.positionX).toBeCloseTo(0);
    expect(next.positionY).toBeCloseTo(142.10526315789474);
    expect(next.scale).toBeCloseTo(1.0526315789473684);
  });

  test('anchors an overflowing axis when the cursor is in viewport padding', () => {
    const geometry = makeGeometry({
      viewportWidth: 800,
      viewportHeight: 600,
      baseDimensions: { width: 900, height: 300 },
      rawDimensions: { width: 900, height: 300 },
      minScale: 0.8888888888888888,
    });

    const next = computeZoomTransform({
      geometry,
      currentTransform: { positionX: -80, positionY: 135, scale: 1.1 },
      zoomRatio: 1.1,
      clientX: 700,
      clientY: 50,
    });

    expect(next.positionX).toBeCloseTo(-158);
    expect(next.positionY).toBeCloseTo(118.5);
    expect(next.scale).toBeCloseTo(1.21);
  });

  test('blends overflowing axes back toward center while zooming out', () => {
    const geometry = makeGeometry({
      viewportWidth: 800,
      viewportHeight: 600,
      baseDimensions: { width: 1600, height: 1200 },
      rawDimensions: { width: 1600, height: 1200 },
      minScale: 0.5,
    });

    const zoomedIn = computeZoomTransform({
      geometry,
      currentTransform: getFitTransform(geometry),
      zoomRatio: 1.1,
      clientX: 700,
      clientY: 500,
    });
    const zoomedOut = computeZoomTransform({
      geometry,
      currentTransform: zoomedIn,
      zoomRatio: 0.95,
      clientX: 700,
      clientY: 500,
    });

    expect(zoomedOut.positionX).toBeCloseTo(-18.6075);
    expect(zoomedOut.positionY).toBeCloseTo(-13.905);
    expect(zoomedOut.scale).toBeCloseTo(0.5225);
  });

  test('anchors one axis or both axes according to overflow state', () => {
    const widthOnlyGeometry = makeGeometry({
      viewportWidth: 800,
      viewportHeight: 600,
      baseDimensions: { width: 760, height: 300 },
      rawDimensions: { width: 760, height: 300 },
      minScale: 1,
    });

    const widthAtEdge = computeZoomTransform({
      geometry: widthOnlyGeometry,
      currentTransform: { positionX: 20, positionY: 150, scale: 1 },
      zoomRatio: 1.1,
      clientX: 750,
      clientY: 300,
    });
    const widthAnchored = computeZoomTransform({
      geometry: widthOnlyGeometry,
      currentTransform: widthAtEdge,
      zoomRatio: 1.1,
      clientX: 750,
      clientY: 300,
    });

    expect(widthAnchored.positionX).toBeCloseTo(-75);
    expect(widthAnchored.positionY).toBeCloseTo(126.31578947368419);

    const bothAxisGeometry = makeGeometry({
      viewportWidth: 800,
      viewportHeight: 600,
      baseDimensions: { width: 900, height: 700 },
      rawDimensions: { width: 900, height: 700 },
      minScale: 0.8571428571428571,
    });

    const bothAtEdge = computeZoomTransform({
      geometry: bothAxisGeometry,
      currentTransform: getFitTransform(bothAxisGeometry),
      zoomRatio: 1.1,
      clientX: 700,
      clientY: 500,
    });
    const bothAnchored = computeZoomTransform({
      geometry: bothAxisGeometry,
      currentTransform: bothAtEdge,
      zoomRatio: 1.1,
      clientX: 700,
      clientY: 500,
    });

    expect(bothAnchored.positionX).toBeCloseTo(-70);
    expect(bothAnchored.positionY).toBeCloseTo(-70.37037037037032);
  });
});
