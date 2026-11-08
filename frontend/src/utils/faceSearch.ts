import { ROUTES } from '@/constants/routes';

// Face search reuses the text search results page, in its own "face" mode.
export const FACE_SEARCH_MODE = 'face';
export const FACE_SEARCH_PATH = `/${ROUTES.SEARCH}?mode=${FACE_SEARCH_MODE}`;

export const isFaceSearchLocation = (location: {
  pathname: string;
  search: string;
}): boolean =>
  location.pathname === `/${ROUTES.SEARCH}` &&
  new URLSearchParams(location.search).get('mode') === FACE_SEARCH_MODE;
