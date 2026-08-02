import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router';

// Import modular components
import FolderManagementCard from './components/FolderManagementCard';
import UserPreferencesCard from './components/UserPreferencesCard';
import ApplicationControlsCard from './components/ApplicationControlsCard';
import AccountSettingsCard from './components/AccountSettingsCard';
import SystemSettingsCard from './components/SystemSettingsCard';

/**
 * Settings page component
 * Acts as an orchestrator for the settings sections
 */
const Settings: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('general');

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    navigate(`#${tab}`, { replace: true });
  };

  useEffect(() => {
    const hash = location.hash;
    if (hash === '#account') {
      setActiveTab('account');
    } else if (hash === '#general') {
      setActiveTab('general');
    } else if (hash === '') {
      setActiveTab('general');
      navigate(`#general`, { replace: true });
    }
  }, [location.hash]);
  const baseTabStyle = 'px-4 py-2 rounded-md font-medium transition-colors';
  const activeTabStyle = 'bg-background text-foreground';
  const inactiveTabStyle =
    'text-muted-foreground hover:bg-gray-100 dark:hover:bg-gray-800';
  return (
    <>
      <h1 className="my-6 text-2xl font-bold">Settings</h1>
      <div className="flex-1 pr-3">
        <div className="flex flex-col space-y-8">
          <div
            className="bg-card flex w-fit items-center justify-center gap-1 rounded-lg border p-1"
            role="tablist"
          >
            <button
              role="tab"
              aria-selected={activeTab === 'general'}
              aria-controls="general-panel"
              onClick={() => handleTabChange('general')}
              className={`${baseTabStyle} ${activeTab === 'general' ? activeTabStyle : inactiveTabStyle}`}
            >
              General
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'account'}
              aria-controls="account-panel"
              onClick={() => handleTabChange('account')}
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
                <SystemSettingsCard />
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
