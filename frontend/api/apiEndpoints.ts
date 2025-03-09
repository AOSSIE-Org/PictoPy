import { BACKED_URL } from '../src/Config/Backend';

export const imagesEndpoints = {
  allImages: `${BACKED_URL}/images/all-images`,
  deleteMultipleImages: `${BACKED_URL}/images/multiple-images`,
  allImageObjects: `${BACKED_URL}/images/all-image-objects`,
  addFolder: `${BACKED_URL}/images/add-folder`,
  addMultipleImages: `${BACKED_URL}/images/multiple-images`,
  generateThumbnails: `${BACKED_URL}/images/generate-thumbnails`,
  deleteThumbnails: `${BACKED_URL}/images/delete-thumbnails`,
};

export const albumEndpoints = {
  createAlbum: `${BACKED_URL}/albums/create-album`,
  deleteAlbum: `${BACKED_URL}/albums/delete-album`,
  viewAllAlbums: `${BACKED_URL}/albums/view-all`,
  addToAlbum: `${BACKED_URL}/albums/add-to-album`,
  addMultipleToAlbum: `${BACKED_URL}/albums/add-multiple-to-album`,
  removeFromAlbum: `${BACKED_URL}/albums/remove-from-album`,
  viewAlbum: `${BACKED_URL}/albums/view-album`,
  editAlbumDescription: `${BACKED_URL}/albums/edit-album-description`,
  addMultipleToAlbums: `${BACKED_URL}/albums/multiple-images`,
};

export const faceTaggingEndpoints = {
  match: `${BACKED_URL}/tag/match`,
  clusters: `${BACKED_URL}/tag/clusters`,
  relatedImages: `${BACKED_URL}/tag/related-images`,
  searchByFace: `${BACKED_URL}/tag/search-by-face`,
};
