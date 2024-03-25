const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld("dbConsultas", {
  listar: () => ipcRenderer.invoke("canal:listar"),
  crear: (newGalleryItem, localPath) => ipcRenderer.invoke("canal:crear", newGalleryItem, localPath),
  editar: (editGalleryItem, idImg) => ipcRenderer.invoke("canal:editar", editGalleryItem, idImg),
  eliminar: (idImg, imgSrc) => ipcRenderer.invoke("canal:eliminar", idImg, imgSrc)
});