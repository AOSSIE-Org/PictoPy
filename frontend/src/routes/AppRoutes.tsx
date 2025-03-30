import { createBrowserRouter, createRoutesFromElements, Route } from 'react-router-dom';
import { ROUTES } from '@/constants/routes';
import { InitialPage } from '@/pages/Setupscreen/Setup';
import { Layout } from '@/Layout';
import Dashboard from '@/pages/Dashboard/Dashboard';
import Videos from '@/pages/VideosPage/Videos';
import Settings from '@/pages/SettingsPage/Settings';
import AITagging from '@/pages/AITagging/AITaging';
import Album from '@/pages/Album/Album';
import Memories from '@/pages/Memories/Memories';
import SecureFolder from '@/pages/SecureFolderPage/SecureFolder';
import { fetchImagesForHome } from '@/loader/fetchImages';
import { fetchAllImageObjects } from '@/loader/fetchAIImages';
import { fetchAlbums } from '@/loader/fetchAlbums';



export const router = createBrowserRouter(
  createRoutesFromElements(
  <>
    <Route path='' element={<InitialPage/>} />
    <Route path='/' element={<Layout/>} >
        <Route 
          path={ROUTES.LAYOUT.HOME} 
          element={<Dashboard/>} 
          loader={fetchImagesForHome}  
        />
        <Route 
          path={ROUTES.LAYOUT.VIDEOS} 
          element={<Videos />} 
        />
        <Route 
          path={ROUTES.LAYOUT.SETTINGS} 
          element={<Settings />} 
        />
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
        <Route 
          path={ROUTES.LAYOUT.SECURE_FOLDER} 
          element={<SecureFolder />} 
        />
        <Route 
          path={ROUTES.LAYOUT.MEMORIES} 
          element={<Memories />} 
        />
    </Route>
  </>
  )
)

