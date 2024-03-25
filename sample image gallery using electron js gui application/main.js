const { app, BrowserWindow, ipcMain } = require('electron');
const {listar, crear, editar, eliminar} = require('./src/db/db-consultas.js');
const { randomUUID } = require('crypto');
const path = require("path");
const fs = require('fs');

function createWindow () {
  const win = new BrowserWindow({
    icon: path.join(__dirname, 'icon.ico'),
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'src', 'preload.js')
    }
  })

  win.loadFile(path.join(__dirname, 'src', 'index.html'));
  win.maximize();
  // win.webContents.openDevTools();
}

app.whenReady().then(() => {
  ipcMain.handle("canal:listar", listar);
  ipcMain.handle("canal:crear", createNewImg);
  ipcMain.handle("canal:editar", (e, editGalleryItem, idImg) => editar(editGalleryItem, idImg));
  ipcMain.handle("canal:eliminar", deleteImg);
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})


async function createNewImg(e, newGalleryItem, localPath){
  const fileExt = path.extname(localPath);
  const filename = `${randomUUID()}${fileExt}`;
  newGalleryItem.imgPath = filename;
  fs.writeFileSync(path.join(__dirname, 'img' , filename), fs.readFileSync(localPath));
  newGalleryItem.idImg = (await crear(newGalleryItem)).insertId;
  return newGalleryItem;
};

function deleteImg(e, idImg, imgSrc) {
  eliminar(idImg);
  fs.unlinkSync(path.join(__dirname, imgSrc.replace('../', '')));
};