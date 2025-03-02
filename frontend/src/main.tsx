import React,{useState,useEffect} from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { isProd } from './utils/isProd';
import { stopServer, startServer } from './utils/serverUtils';
import { getCurrentWindow } from '@tauri-apps/api/window';

//Listen for window close event and stop server
const onCloseListener = async () => {
  await getCurrentWindow().onCloseRequested(async () => {
    await stopServer();
  });
};

const fetchFilePath = async () => {
  try {
    // Fetch file path from backend
    const response = await fetch("http://localhost:8000/images/get-thumbnail-path");
    const data = await response.json();

    if (data.thumbnailPath) {
      // Store in localStorage
      localStorage.setItem("thumbnailPath", data.thumbnailPath);
      return data.thumbnailPath;
    }
  } catch (error) {
    console.error("Error fetching file path:", error);
  }
  return null;
};

const Main = () => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      const storedPath = localStorage.getItem("thumbnailPath");
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
