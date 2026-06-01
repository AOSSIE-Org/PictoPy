import React, { useEffect, useState } from 'react';
import { Monitor } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import SettingsCard from './SettingsCard';

const SystemSettingsCard: React.FC = () => {
  const [autostart, setAutostart] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    invoke<boolean>('is_autostart_enabled')
      .then(setAutostart)
      .catch(() => setAutostart(false))
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = async () => {
    const next = !autostart;
    try {
      await invoke(next ? 'enable_autostart' : 'disable_autostart');
      setAutostart(next);
    } catch (err) {
      console.error('Failed to toggle autostart:', err);
    }
  };

  return (
    <SettingsCard
      icon={Monitor}
      title="System"
      description="System integration and startup behavior"
    >
      <div className="flex items-center justify-between py-1">
        <div>
          <div className="font-medium">Launch at startup</div>
          <div className="text-muted-foreground text-sm">
            Automatically start PictoPy when you log in. The window starts
            minimized to the system tray.
          </div>
        </div>

        <button
          role="switch"
          aria-checked={autostart}
          disabled={loading}
          onClick={handleToggle}
          className={[
            'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full',
            'transition-colors duration-200 ease-in-out',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            autostart
              ? 'bg-primary focus-visible:ring-primary'
              : 'bg-gray-200 focus-visible:ring-gray-500 dark:bg-gray-700',
          ].join(' ')}
        >
          <span
            className={[
              'inline-block h-4 w-4 rounded-full bg-white shadow-md',
              'transition-transform duration-200 ease-in-out',
              autostart ? 'translate-x-6' : 'translate-x-1',
            ].join(' ')}
          />
        </button>
      </div>
    </SettingsCard>
  );
};

export default SystemSettingsCard;
