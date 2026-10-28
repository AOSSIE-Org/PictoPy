import React, { useEffect, useState } from 'react';
import { Monitor } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import SettingsCard from './SettingsCard';
import { Switch } from '@/components/ui/switch';

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

          <Switch
          checked={isChecked}
          onCheckedChange={handleToggle}
          disabled={isDisabled}
          aria-labelledby="autostart-label"
          aria-describedby="autostart-desc"
        />
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

          <Switch
          checked={closeToTrayChecked}
          onCheckedChange={handleCloseToTrayToggle}
          disabled={closeToTrayDisabled}
          aria-labelledby="close-to-tray-label"
          aria-describedby="close-to-tray-desc"
        />
      </div>
    </SettingsCard>
  );
};

export default SystemSettingsCard;
