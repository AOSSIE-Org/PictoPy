import React, { useEffect, useState } from 'react';
import { Monitor } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import SettingsCard from './SettingsCard';

const SystemSettingsCard: React.FC = () => {
  // null = unknown / error reading state
  const [autostart, setAutostart] = useState<boolean | null>(null);
  const [closeToTray, setCloseToTray] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [pendingCloseToTray, setPendingCloseToTray] = useState(false);

  useEffect(() => {
    Promise.all([
      invoke<boolean>('is_autostart_enabled')
        .then(setAutostart)
        .catch(() => setAutostart(null)),
      invoke<boolean>('get_close_to_tray')
        .then(setCloseToTray)
        .catch(() => setCloseToTray(null)),
    ]).finally(() => setLoading(false));
  }, []);

  const handleToggle = async () => {
    if (autostart === null) return;
    const next = !autostart;
    setPending(true);
    try {
      await invoke(next ? 'enable_autostart' : 'disable_autostart');
      setAutostart(next);
    } catch (err) {
      console.error('Failed to toggle autostart:', err);
    } finally {
      setPending(false);
    }
  };

  const handleCloseToTrayToggle = async () => {
    if (closeToTray === null) return;
    const next = !closeToTray;
    setPendingCloseToTray(true);
    try {
      await invoke('set_close_to_tray', { enabled: next });
      setCloseToTray(next);
    } catch (err) {
      console.error('Failed to toggle close-to-tray:', err);
    } finally {
      setPendingCloseToTray(false);
    }
  };

  const isDisabled = loading || pending || autostart === null;
  const isChecked = autostart === true;

  const closeToTrayDisabled =
    loading || pendingCloseToTray || closeToTray === null;
  const closeToTrayChecked = closeToTray === true;

  return (
    <SettingsCard
      icon={Monitor}
      title="System"
      description="System integration and startup behavior"
    >
      <div className="flex items-center justify-between py-1">
        <div>
          <div id="autostart-label" className="font-medium">
            Launch at startup
          </div>
          <div id="autostart-desc" className="text-muted-foreground text-sm">
            Automatically start PictoPy when you log in. The window starts
            minimized to the system tray.
          </div>
        </div>

        <button
          role="switch"
          aria-checked={isChecked}
          aria-labelledby="autostart-label"
          aria-describedby="autostart-desc"
          disabled={isDisabled}
          onClick={handleToggle}
          className={[
            'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full',
            'transition-colors duration-200 ease-in-out',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            isChecked
              ? 'bg-primary focus-visible:ring-primary'
              : 'bg-gray-200 focus-visible:ring-gray-500 dark:bg-gray-700',
          ].join(' ')}
        >
          <span
            className={[
              'inline-block h-4 w-4 rounded-full bg-white shadow-md',
              'transition-transform duration-200 ease-in-out',
              isChecked ? 'translate-x-6' : 'translate-x-1',
            ].join(' ')}
          />
        </button>
      </div>

      <div className="flex items-center justify-between py-1">
        <div>
          <div id="close-to-tray-label" className="font-medium">
            Close to tray
          </div>
          <div
            id="close-to-tray-desc"
            className="text-muted-foreground text-sm"
          >
            When enabled, closing the window hides the app to the system tray
            instead of exiting.
          </div>
        </div>

        <button
          role="switch"
          aria-checked={closeToTrayChecked}
          aria-labelledby="close-to-tray-label"
          aria-describedby="close-to-tray-desc"
          disabled={closeToTrayDisabled}
          onClick={handleCloseToTrayToggle}
          className={[
            'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full',
            'transition-colors duration-200 ease-in-out',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            closeToTrayChecked
              ? 'bg-primary focus-visible:ring-primary'
              : 'bg-gray-200 focus-visible:ring-gray-500 dark:bg-gray-700',
          ].join(' ')}
        >
          <span
            className={[
              'inline-block h-4 w-4 rounded-full bg-white shadow-md',
              'transition-transform duration-200 ease-in-out',
              closeToTrayChecked ? 'translate-x-6' : 'translate-x-1',
            ].join(' ')}
          />
        </button>
      </div>
    </SettingsCard>
  );
};

export default SystemSettingsCard;
