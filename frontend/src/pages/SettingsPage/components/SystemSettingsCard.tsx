import React, { useEffect, useState } from 'react';
import { Monitor } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import SettingsCard from './SettingsCard';
import SettingSwitchRow from './SettingSwitchRow';

const SystemSettingsCard: React.FC = () => {
  // null = unknown / error reading state
  const [autostart, setAutostart] = useState<boolean | null>(null);
  const [closeToTray, setCloseToTray] = useState<boolean | null>(null);
  const [startMinimized, setStartMinimized] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [pendingCloseToTray, setPendingCloseToTray] = useState(false);
  const [pendingStartMinimized, setPendingStartMinimized] = useState(false);

  useEffect(() => {
    Promise.all([
      invoke<boolean>('is_autostart_enabled')
        .then(setAutostart)
        .catch(() => setAutostart(null)),
      invoke<boolean>('get_close_to_tray')
        .then(setCloseToTray)
        .catch(() => setCloseToTray(null)),
      invoke<boolean>('get_start_minimized')
        .then(setStartMinimized)
        .catch(() => setStartMinimized(null)),
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

  const handleStartMinimizedToggle = async () => {
    if (startMinimized === null) return;
    const next = !startMinimized;
    setPendingStartMinimized(true);
    try {
      await invoke('set_start_minimized', { enabled: next });
      setStartMinimized(next);
    } catch (err) {
      console.error('Failed to toggle start minimized:', err);
    } finally {
      setPendingStartMinimized(false);
    }
  };

  const isDisabled = loading || pending || autostart === null;
  const isChecked = autostart === true;

  const closeToTrayDisabled =
    loading || pendingCloseToTray || closeToTray === null;
  const closeToTrayChecked = closeToTray === true;

  const startMinimizedDisabled =
    loading || pendingStartMinimized || startMinimized === null;
  const startMinimizedChecked = startMinimized === true;

  const autostartDescription = startMinimizedChecked
    ? 'Automatically start PictoPy when you log in. The window starts minimized to the system tray.'
    : 'Automatically start PictoPy when you log in. The main window opens directly on boot.';

  return (
    <SettingsCard
      icon={Monitor}
      title="System"
      description="System integration and startup behavior"
    >
      <SettingSwitchRow
        id="autostart"
        label="Launch at startup"
        description={autostartDescription}
        checked={isChecked}
        disabled={isDisabled}
        onToggle={handleToggle}
      />

      {isChecked && (
        <SettingSwitchRow
          id="start-minimized"
          label="Start minimized"
          description="When enabled, PictoPy starts silently in the system tray on boot. When disabled, the main window opens on boot instead."
          checked={startMinimizedChecked}
          disabled={startMinimizedDisabled}
          onToggle={handleStartMinimizedToggle}
        />
      )}

      <SettingSwitchRow
        id="close-to-tray"
        label="Close to tray"
        description="When enabled, closing the window hides the app to the system tray instead of exiting."
        checked={closeToTrayChecked}
        disabled={closeToTrayDisabled}
        onToggle={handleCloseToTrayToggle}
      />
    </SettingsCard>
  );
};

export default SystemSettingsCard;
