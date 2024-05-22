const { app, BrowserWindow } = require('electron')
const path = require('node:path')



const createWindow = () => {
    const win = new BrowserWindow({
      width: 800,
      height: 600,
      webPreferences: {
        preload: path.join(__dirname, 'src/preload.js')
      }

    })
  
    win.loadFile('src/index.html')
  }

  app.whenReady().then(() => {
    createWindow()
  
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
  })