import React from 'react';

// Import modular components
import FolderManagementCard from './components/FolderManagementCard';
import UserPreferencesCard from './components/UserPreferencesCard';

import ApplicationControlsCard from './components/ApplicationControlsCard';

/**
 * Settings page component
 * Acts as an orchestrator for the settings sections
 */
const Settings: React.FC = () => {
  return (
    <div className="mx-auto flex-1 px-8 py-6">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Folder Management */}
        <FolderManagementCard />

        {/* User Preferences */}
        <UserPreferencesCard />



        {/* Application Controls */}
        <ApplicationControlsCard />
      </div>
    </div>
  );
};

export default Settings;
