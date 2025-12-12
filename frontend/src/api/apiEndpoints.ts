export const imagesEndpoints = {
  getAllImages: '/images/',
  setFavourite: '/images/toggle-favourite',
  getThumbnail: (imageId: string) => `/images/${imageId}/thumbnail`,
  getFullImage: (imageId: string) => `/images/${imageId}`,
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

export const smartAlbumsEndpoints = {
  // Get all smart albums
  getAllAlbums: '/smart-albums/albums',
  
  // Get specific album details
  getAlbumDetails: (albumId: string) => `/smart-albums/${albumId}`,
  
  // Get images in an album (with pagination)
  getAlbumImages: (albumId: string, limit?: number, offset?: number) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const query = params.toString();
    return `/smart-albums/${albumId}/images${query ? '?' + query : ''}`;
  },
  
  // Create object-based smart album
  createObjectAlbum: '/smart-albums/create_object_album',
  
  // Create face-based smart album
  createFaceAlbum: '/smart-albums/create_face_album',
  
  // Create predefined albums (People, Animals, Vehicles, etc.)
  createPredefinedAlbums: '/smart-albums/predefine_smart_albums',
  
  // Refresh single album
  refreshAlbum: (albumId: string) => `/smart-albums/${albumId}/refresh`,
  
  // Refresh all albums
  refreshAllAlbums: '/smart-albums/refresh_all',
  
  // Update album (name, auto_update)
  updateAlbum: (albumId: string) => `/smart-albums/${albumId}`,
  
  // Delete album
  deleteAlbum: (albumId: string) => `/smart-albums/${albumId}`,
  
  // Get available YOLO object classes
  getAvailableClasses: '/smart-albums/classes/available',
  
  // Get album statistics
  getStatistics: '/smart-albums/stats/overview',
};
