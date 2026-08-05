export const imagesEndpoints = {
  getAllImages: '/images/',
  setFavourite: '/images/toggle-favourite',
  searchByTag: (tag: string) => `/images/search?tag=${encodeURIComponent(tag)}`,
  semanticSearch: (query: string) =>
    `/images/semantic-search?query=${encodeURIComponent(query)}`,
};

export const videosEndpoints = {
  getAllVideos: '/videos/',
  setFavourite: '/videos/toggle-favourite',
  searchByTag: (tag: string) => `/videos/search?tag=${encodeURIComponent(tag)}`,
  semanticSearch: (query: string) =>
    `/videos/semantic-search?query=${encodeURIComponent(query)}`,
  purgeFrameCache: '/videos/purge-frame-cache',
};

export const faceClustersEndpoints = {
  getAllClusters: '/face-clusters/',
  searchForFaces: '/face-clusters/face-search?input_type=path',
  searchForFacesBase64: '/face-clusters/face-search?input_type=base64',
  renameCluster: (clusterId: string) => `/face-clusters/${clusterId}`,
  getClusterImages: (clusterId: string) => `/face-clusters/${clusterId}/images`,
  globalRecluster: '/face-clusters/global-recluster',
  globalReclusterStatus: (taskId: string) =>
    `/face-clusters/global-recluster/${taskId}`,
  multiPersonSearch: '/face-clusters/multi-search',
};

export const foldersEndpoints = {
  getAllFolders: '/folders/all-folders',
  addFolder: '/folders/add-folder',
  enableAITagging: '/folders/enable-ai-tagging',
  disableAITagging: '/folders/disable-ai-tagging',
  deleteFolders: '/folders/delete-folders',
  syncFolder: '/folders/sync-folder',
  getTaggingStatus: '/folders/status',
};

export const userPreferencesEndpoints = {
  getUserPreferences: '/user-preferences/',
  updateUserPreferences: '/user-preferences/',
};

export const healthEndpoints = {
  healthCheck: '/health',
};

export const albumsEndpoints = {
  getAllAlbums: '/albums/',
  getAlbumById: (albumId: string) => `/albums/${albumId}`,
  createAlbum: '/albums/',
  createAlbumFromMemory: '/albums/from-memory',
  updateAlbum: (albumId: string) => `/albums/${albumId}`,
  deleteAlbum: (albumId: string) => `/albums/${albumId}`,
  addImagesToAlbum: (albumId: string) => `/albums/${albumId}/images`,
  getAlbumImages: (albumId: string) => `/albums/${albumId}/images/get`,
  removeImageFromAlbum: (albumId: string, imageId: string) =>
    `/albums/${albumId}/images/${imageId}`,
  removeMultipleImagesFromAlbum: (albumId: string) =>
    `/albums/${albumId}/images`,
};

export const memoriesEndpoints = {
  list: '/memories',
  generate: '/memories/generate',
  status: '/memories/status',
  today: '/memories/today',
  byId: (memoryId: string) => `/memories/${memoryId}`,
};
