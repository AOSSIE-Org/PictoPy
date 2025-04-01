import { useState, useEffect } from 'react';
import { save } from '@tauri-apps/plugin-dialog';

export function useTauriCheck() {
  const [isTauri, setIsTauri] = useState(false);
  const [dialogAvailable, setDialogAvailable] = useState(false);

  useEffect(() => {
    const checkTauri = () => {
      const isTauriEnv =
        typeof window !== 'undefined' &&
        ((window as any).__TAURI__ !== undefined ||
          window.location.port === '1420');
      setIsTauri(!!isTauriEnv);
      setDialogAvailable(isTauriEnv && typeof save === 'function');
    };

    checkTauri();
  }, []);

  return { isTauri, dialogAvailable };
}
