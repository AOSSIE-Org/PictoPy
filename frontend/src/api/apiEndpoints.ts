export const imagesEndpoints = {
  getAllImages: '/images/',
  setFavourite: '/images/toggle-favourite',
};

export const faceClustersEndpoints = {
  getAllClusters: '/face-clusters/',
  searchForFaces: '/face-clusters/face-search?input_type=path',
  searchForFacesBase64: '/face-clusters/face-search?input_type=base64',
  renameCluster: (clusterId: string) => `/face-clusters/${clusterId}`,
  getClusterImages: (clusterId: string) => `/face-clusters/${clusterId}/images`,
  globalRecluster: '/face-clusters/global-recluster',
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
