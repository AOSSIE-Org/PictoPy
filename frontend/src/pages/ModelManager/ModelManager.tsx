import React, { useState, useEffect } from 'react';
import { SidebarProvider } from '@/components/ui/sidebar';
import { ModelManagerSidebar, TabConfig } from './ModelManagerSidebar';
import { InstalledTab } from './InstalledTab';
import { AvailableTab } from './AvailableTab';
import { Download, Cloud } from 'lucide-react';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchModelStatus } from '@/api/api-functions';

const TABS: TabConfig[] = [
  { id: 'Installed', label: 'Installed', icon: Download },
  { id: 'Available', label: 'Available', icon: Cloud },
];

export const ModelManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('Installed');
  const [downloadingTiers, setDownloadingTiers] = useState<Map<string, string>>(
    new Map(),
  );
  const [installedJustNow, setInstalledJustNow] = useState<Set<string>>(
    new Set(),
  );

  const {
    data: statusData,
    isLoading,
    isError,
  } = usePictoQuery({
    queryKey: ['models', 'status'],
    queryFn: fetchModelStatus,
    refetchInterval: downloadingTiers.size > 0 ? 3000 : false,
  });

  // Polling updates statusData which drives AvailableTab's tier filtering.
  // Polling clears downloadingTiers to stop further SSE connections, while
  // installedJustNow in AvailableTab controls whether the completed card stays visible until tab remount.
  useEffect(() => {
    if (statusData?.data && downloadingTiers.size > 0) {
      const newDownloading = new Map(downloadingTiers);
      const newInstalledJustNow = new Set(installedJustNow);
      let changed = false;

      for (const [tier] of downloadingTiers) {
        const modelsArr = Object.values(statusData.data);
        const objModel = modelsArr.find(
          (m) => m.tier === tier && m.feature === 'object_detection',
        );
        const faceModel = modelsArr.find(
          (m) => m.tier === tier && m.feature === 'face_detection',
        );

        if (objModel?.installed && faceModel?.installed) {
          newInstalledJustNow.add(tier);
          newDownloading.delete(tier);
          changed = true;
        }
      }

      if (changed) {
        setInstalledJustNow(newInstalledJustNow);
        setDownloadingTiers(newDownloading);
      }
    }
  }, [statusData, downloadingTiers, installedJustNow]);

  const handleTabChange = (newTab: string) => {
    if (activeTab === 'Available' && newTab !== 'Available') {
      setInstalledJustNow(new Set());
    }
    setActiveTab(newTab);
  };

  return (
    <SidebarProvider>
      <div className="bg-background text-foreground flex h-screen w-full">
        <ModelManagerSidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          tabs={TABS}
        />

        {/* Content Area */}
        <div className="mx-4 my-8 flex-1 overflow-y-auto">
          <h1 className="mb-6 text-2xl font-bold">{activeTab}</h1>

          {activeTab === 'Installed' ? (
            <InstalledTab
              statusData={statusData}
              isLoading={isLoading}
              isError={isError}
            />
          ) : (
            <AvailableTab
              statusData={statusData}
              isLoading={isLoading}
              isError={isError}
              downloadingTiers={downloadingTiers}
              setDownloadingTiers={setDownloadingTiers}
              installedJustNow={installedJustNow}
              setInstalledJustNow={setInstalledJustNow}
            />
          )}
        </div>
      </div>
    </SidebarProvider>
  );
};
