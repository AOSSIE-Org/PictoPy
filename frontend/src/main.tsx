import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import BrowserWarning from './components/BrowserWarning';
import { isTauriEnvironment } from './utils/tauriUtils';
import { store } from './app/store';
import { Provider } from 'react-redux';

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
