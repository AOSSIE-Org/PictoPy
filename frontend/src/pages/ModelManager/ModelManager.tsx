import React, { useState } from 'react';
import { SidebarProvider } from '@/components/ui/sidebar';
import { ModelManagerSidebar, TabConfig } from './ModelManagerSidebar';
import { InstalledTab } from './InstalledTab';
import { Download, Cloud, Activity } from 'lucide-react';

const TABS: TabConfig[] = [
  { id: 'Installed', label: 'Installed', icon: Download },
  { id: 'Available', label: 'Available', icon: Cloud },
  { id: 'Activity', label: 'Activity', icon: Activity },
];

export const ModelManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('Installed');

  return (
    <SidebarProvider>
      <div className="bg-background text-foreground flex h-screen w-full">
        <ModelManagerSidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={TABS}
        />

        {/* Content Area */}
        <div className="mx-4 my-8 flex-1 overflow-y-auto">
          <h1 className="mb-6 text-2xl font-bold">{activeTab}</h1>

          {activeTab === 'Installed' ? (
            <InstalledTab />
          ) : (
            <div className="bg-card flex min-h-[300px] items-center justify-center rounded-xl border p-8 shadow-sm">
              <p className="text-muted-foreground text-center">
                Content for {activeTab} models will appear here.
              </p>
            </div>
          )}
        </div>
      </div>
    </SidebarProvider>
  );
};
