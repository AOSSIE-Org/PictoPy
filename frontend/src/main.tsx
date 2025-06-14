import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { isProd } from './utils/isProd';
import { stopServer, startServer } from './utils/serverUtils';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { imagesEndpoints } from '../api/apiEndpoints';

//Listen for window close event and stop server
const onCloseListener = async () => {
  await getCurrentWindow().onCloseRequested(async () => {
    await stopServer();
  });
};

const fetchFilePath = async () => {
  try {
    // Fetch file path from backend
    const response = await fetch(imagesEndpoints.getThumbnailPath);
    const data = await response.json();
    if (localStorage.getItem('thumbnailPath')) {
      localStorage.removeItem('thumbnailPath');
    }
    if (data.thumbnailPath) {
      // Store in localStorage
      console.log('Thumbnail Path = ', data.thumbnailPath);
      localStorage.setItem('thumbnailPath', data.thumbnailPath);
      return data.thumbnailPath;
    }
  } catch (error) {
    console.error('Error fetching file path:', error);
  }
  return null;
};

const Main = () => {
  useEffect(() => {
    const init = async () => {
      const storedPath = localStorage.getItem('thumbnailPath');
      console.log('Thumbnail Path = ', storedPath);
      if (!storedPath) {
        await fetchFilePath();
      }
    };

    init();
  }, []);

  return <App />;
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Main />
  </React.StrictMode>,
);

if (isProd()) {
  onCloseListener();
  console.log('Starting PictoPy Server');
  startServer();
}
