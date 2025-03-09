import { BACKEND_URL } from '../src/Config/Backend';

export const imagesEndpoints = {
  allImages: `${BACKEND_URL}/images/all-images`,
  deleteMultipleImages: `${BACKEND_URL}/images/multiple-images`,
  allImageObjects: `${BACKEND_URL}/images/all-image-objects`,
  addFolder: `${BACKEND_URL}/images/add-folder`,
  addMultipleImages: `${BACKEND_URL}/images/multiple-images`,
  generateThumbnails: `${BACKEND_URL}/images/generate-thumbnails`,
  deleteThumbnails: `${BACKEND_URL}/images/delete-thumbnails`,
};

export const albumEndpoints = {
  createAlbum: `${BACKEND_URL}/albums/create-album`,
  deleteAlbum: `${BACKEND_URL}/albums/delete-album`,
  viewAllAlbums: `${BACKEND_URL}/albums/view-all`,
  addToAlbum: `${BACKEND_URL}/albums/add-to-album`,
  addMultipleToAlbum: `${BACKEND_URL}/albums/add-multiple-to-album`,
  removeFromAlbum: `${BACKEND_URL}/albums/remove-from-album`,
  viewAlbum: `${BACKEND_URL}/albums/view-album`,
  editAlbumDescription: `${BACKEND_URL}/albums/edit-album-description`,
  addMultipleToAlbums: `${BACKEND_URL}/albums/multiple-images`,
};

export const faceTaggingEndpoints = {
  match: `${BACKED_URL}/tag/match`,
  clusters: `${BACKED_URL}/tag/clusters`,
  relatedImages: `${BACKED_URL}/tag/related-images`,
  searchByFace: `${BACKED_URL}/tag/search-by-face`,
};
