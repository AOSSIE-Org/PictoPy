import React, { useState } from 'react';

// Import modular components
import FolderManagementCard from './components/FolderManagementCard';
import UserPreferencesCard from './components/UserPreferencesCard';
import ApplicationControlsCard from './components/ApplicationControlsCard';
import AccountSettingsCard from './components/AccountSettingsCard';

/**
 * Settings page component
 * Acts as an orchestrator for the settings sections
 */
const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('general');
  const baseTabStyle = 'px-4 py-2 rounded-md font-medium transition-colors';
  const activeTabStyle = 'bg-background text-foreground';
  const inactiveTabStyle =
    'text-muted-foreground hover:bg-gray-100 dark:hover:bg-gray-800';
  return (
    <>
      <h1 className="mt-6 mb-6 text-2xl font-bold">Settings</h1>
      <div className="mx-auto flex-1 pr-3">
        <div className="mx-auto space-y-8">
          <div className="bg-card w-50 rounded-lg border p-1" role="tablist">
            <button
              role="tab"
              aria-selected={activeTab === 'general'}
              aria-controls="general-panel"
              onClick={() => setActiveTab('general')}
              className={`${baseTabStyle} ${activeTab === 'general' ? activeTabStyle : inactiveTabStyle}`}
            >
              General
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'account'}
              aria-controls="account-panel"
              onClick={() => setActiveTab('account')}
              className={`${baseTabStyle} ${activeTab === 'account' ? activeTabStyle : inactiveTabStyle}`}
            >
              Account
            </button>
          </div>
          <div className="mt-6 space-y-8">
            {activeTab === 'general' && (
              <>
                <FolderManagementCard />
                <UserPreferencesCard />
                <ApplicationControlsCard />
              </>
            )}

            {activeTab === 'account' && (
              <>
                <AccountSettingsCard />
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Settings;
