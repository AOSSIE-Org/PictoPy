import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

// Import modular components
import FolderManagementCard from './components/FolderManagementCard';
import UserPreferencesCard from './components/UserPreferencesCard';
import ApplicationControlsCard from './components/ApplicationControlsCard';

/**
 * Settings page component
 * Acts as an orchestrator for the settings sections
 */
const Settings: React.FC = () => {
  const navigate = useNavigate();

  const handleSignOut = () => {
    // 1. Wipe all local storage (Auth, Folder, Name)
    localStorage.clear();
    // 2. Force a hard reload to reset state and go to Welcome screen
    window.location.href = '/';
  };
  return (
    <div className="mx-auto flex-1 px-8 py-6">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Folder Management */}
        <FolderManagementCard />

        {/* User Preferences */}
        <UserPreferencesCard />

        {/* Application Controls */}
        <ApplicationControlsCard />
        {/* Sign Out Button - Aligned Right */}
        <div className="mt-8 flex justify-end border-t pt-6">
          <Button
            variant="destructive"
            onClick={handleSignOut}
            // Removed 'w-full' to make it a normal rectangle.
            // 'variant="destructive"' provides the red color and hover shade.
          >
            Sign Out
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
