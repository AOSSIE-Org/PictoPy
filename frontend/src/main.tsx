import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { isProd } from './utils/isProd';
import { stopServer, startServer } from './utils/serverUtils';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { imagesEndpoints } from '../api/apiEndpoints';
import { check } from '@tauri-apps/plugin-updater';

const updater = async () => {
  const update = await check();
  if (update) {
    console.log(
      `found update ${update.version} from ${update.date} with notes ${update.body}`,
    );
    let downloaded = 0;
    let contentLength = 0;
    // alternatively we could also call update.download() and update.install() separately
    await update.downloadAndInstall((event) => {
      switch (event.event) {
        case 'Started':
          contentLength = event.data.contentLength
            ? event.data.contentLength
            : 0;
          console.log(`started downloading ${event.data.contentLength} bytes`);
          break;
        case 'Progress':
          downloaded += event.data.chunkLength;
          console.log(`downloaded ${downloaded} from ${contentLength}`);
          break;
        case 'Finished':
          console.log('download finished');
          break;
      }
    });

    console.log('update installed');
    // await relaunch();
  }
};
updater();
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
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      const storedPath = localStorage.getItem('thumbnailPath');
      console.log('Thumbnail Path = ', storedPath);
      if (!storedPath) {
        await fetchFilePath();
      }
      setIsReady(true);
    };

    init();
  }, []);

  if (!isReady) return <p>Loading...</p>;

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
