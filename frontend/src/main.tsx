import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import BrowserWarning from './components/BrowserWarning';
import { isProd } from './utils/isProd';
import { startServer } from './utils/serverUtils';
import { isTauriEnvironment } from './utils/tauriUtils';
import { store } from './app/store';
import { Provider } from 'react-redux';

//Listen for window close event and stop server.
const onCloseListener = async () => {
  if (!isTauriEnvironment()) {
    console.log('Window close listener is only available in Tauri environment');
    return;
  }

  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window');
    await getCurrentWindow().onCloseRequested(async () => {
      // code to stop the server
    });
  } catch (error) {
    console.error('Error setting up close listener:', error);
  }
};

const Main = () => {
  // Show browser warning if not running in Tauri environment
  if (!isTauriEnvironment()) {
    return <BrowserWarning />;
  }

  return (
    <Provider store={store}>
      <App />
    </Provider>
  );
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Main />
  </React.StrictMode>,
);

if (isProd() && isTauriEnvironment()) {
  onCloseListener();
  console.log('Starting PictoPy Server');
  startServer();
}
