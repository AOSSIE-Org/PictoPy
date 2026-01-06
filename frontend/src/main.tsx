import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import BrowserWarning from './components/BrowserWarning';
import { isProd } from './utils/isProd';
import { triggerShutdown, startServer } from './utils/serverUtils';
import { isTauriEnvironment } from './utils/tauriUtils';
import { store } from './app/store';
import { Provider } from 'react-redux';

// Window close listener triggers backend shutdown.
const onCloseListener = async () => {
  if (!isTauriEnvironment()) {
    console.log('Window close listener is only available in Tauri environment');
    return;
  }

  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window');
    await getCurrentWindow().onCloseRequested(async () => {
      triggerShutdown();
    });
  } catch (error) {
    console.error('Error setting up close listener:', error);
  }
};

const Main = () => {
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

/*
 * Set up shutdown listener and auto-start server ONLY in production mode
 * In dev mode, backend/sync are managed separately via terminal
 */
if (isTauriEnvironment() && isProd()) {
  onCloseListener();
  console.log('Starting PictoPy Server (production mode)');
  startServer().catch((error) => {
    console.error('Failed to start server:', error);
  });
} else if (isTauriEnvironment()) {
  console.log('Dev mode: Backend shutdown managed separately');
}
