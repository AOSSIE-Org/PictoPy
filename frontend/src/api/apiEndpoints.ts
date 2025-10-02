export const imagesEndpoints = {
  getAllImages: '/images/',
};

export const faceClustersEndpoints = {
  getAllClusters: '/face-clusters/',
  searchForFaces: '/face-clusters/face-search',
  renameCluster: (clusterId: string) => `/face-clusters/${clusterId}`,
  getClusterImages: (clusterId: string) => `/face-clusters/${clusterId}/images`,
};

export const foldersEndpoints = {
  getAllFolders: '/folders/all-folders',
  addFolder: '/folders/add-folder',
  enableAITagging: '/folders/enable-ai-tagging',
  disableAITagging: '/folders/disable-ai-tagging',
  deleteFolders: '/folders/delete-folders',
  syncFolder: '/folders/sync-folder',
};

export const userPreferencesEndpoints = {
  getUserPreferences: '/user-preferences/',
  updateUserPreferences: '/user-preferences/',
};

export const albumsEndpoints = {
  getAllAlbums: '/albums/',
  createAlbum: '/albums/',
  getAlbum: (albumId: string) => `/albums/${albumId}`,
  updateAlbum: (albumId: string) => `/albums/${albumId}`,
  deleteAlbum: (albumId: string) => `/albums/${albumId}`,
  getAlbumImages: (albumId: string) => `/albums/${albumId}/images/get`,
  addImagesToAlbum: (albumId: string) => `/albums/${albumId}/images`,
  removeImageFromAlbum: (albumId: string, imageId: string) => `/albums/${albumId}/images/${imageId}`,
  removeImagesFromAlbum: (albumId: string) => `/albums/${albumId}/images`,
};

export const healthEndpoints = {
  healthCheck: '/health',
};
