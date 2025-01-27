import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { isProd } from '@/utils/isProd';
import { stopServer, startServer } from './utils/serverUtils';
import { getCurrentWindow } from '@tauri-apps/api/window';

//Listen for window close event and stop server
const onCloseListener = async () => {
  await getCurrentWindow().onCloseRequested(async () => {
    await stopServer();
  });
};
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

if (isProd()) {
  onCloseListener();
  console.log('Starting PictoPy Server');
  startServer();
}
