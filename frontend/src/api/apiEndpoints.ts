export const imagesEndpoints = {
  getAllImages: '/images/',
};

export const faceClustersEndpoints = {
  getAllClusters: '/face-clusters/',
  renameCluster: (clusterId: string) => `/face-clusters/${clusterId}`,
  getClusterImages: (clusterId: string) => `/face-clusters/${clusterId}/images`,
};

export const foldersEndpoints = {
  addFolder: '/folders/add-folder',
  enableAITagging: '/folders/enable-ai-tagging',
  disableAITagging: '/folders/disable-ai-tagging',
  deleteFolders: '/folders/delete-folders',
  syncFolder: '/folders/sync-folder',
};
