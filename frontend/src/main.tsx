import React from 'react';
import ReactDOM from 'react-dom/client';
import { isProd } from './utils/isProd';
import { stopServer, startServer } from './utils/serverUtils';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { Layout } from './Layout';
import { createBrowserRouter, createRoutesFromElements, Route, RouterProvider } from 'react-router-dom';
import { InitialPage } from './pages/Setupscreen/Setup';
import Dashboard from './pages/Dashboard/Dashboard';
import Videos from './pages/VideosPage/Videos';
import Settings from './pages/SettingsPage/Settings';
import AITagging from './pages/AITagging/AITaging';
import Album from './pages/Album/Album';
import SecureFolder from './pages/SecureFolderPage/SecureFolder';
import Memories from './pages/Memories/Memories';
// import { fetchImages } from './loader/fetchImage';
import { fetchImagesForHome } from './loader/fetchImages';
import { fetchAlbums } from './loader/fetchAlbums';
import { fetchAllImageObjects } from './loader/fetchAIImages';


//Listen for window close event and stop server
const onCloseListener = async () => {
  await getCurrentWindow().onCloseRequested(async () => {
    await stopServer();
  });
};

const ROUTES = {
  INITIAL: '/',
  LAYOUT: {
    AI: 'ai-tagging',
    HOME: 'home',
    DASHBOARD: 'dashboard',
    PHOTOS: 'photos',
    VIDEOS: 'videos',
    SETTINGS: 'settings',
    ALBUM: 'albums',
    SECURE_FOLDER: 'secure-folder',
    MEMORIES: 'memories',
  },
};



const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path='/' element={<Layout/>} >
        <Route path='' element={<InitialPage/>} />
        <Route 
          path='home' 
          element={<Dashboard/>} 
          loader={fetchImagesForHome}  
        />
        <Route path={ROUTES.LAYOUT.VIDEOS} element={<Videos />} />
        <Route path={ROUTES.LAYOUT.SETTINGS} element={<Settings />} />
        <Route 
          path={ROUTES.LAYOUT.AI} 
          element={<AITagging />} 
          loader={fetchAllImageObjects}
        />
        <Route 
          path={ROUTES.LAYOUT.ALBUM} 
          element={<Album/>} 
          loader={fetchAlbums}
        />
        <Route path={ROUTES.LAYOUT.SECURE_FOLDER} element={<SecureFolder />} />
        <Route path={ROUTES.LAYOUT.MEMORIES} element={<Memories />} />
    </Route>
  )
)



ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <RouterProvider router={router} />   
  </React.StrictMode>,
);

if (isProd()) {
  onCloseListener();
  console.log('Starting PictoPy Server');
  startServer();
}
