import React, { useState, useEffect } from 'react';
import { getVersion } from '@tauri-apps/api/app';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { LucideIcon } from 'lucide-react';

export interface TabConfig {
  id: string;
  label: string;
  icon: LucideIcon;
}

interface ModelManagerSidebarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  tabs: TabConfig[];
}

export const ModelManagerSidebar: React.FC<ModelManagerSidebarProps> = ({
  activeTab,
  onTabChange,
  tabs,
}) => {
  const [version, setVersion] = useState<string>('1.0.0');

  useEffect(() => {
    getVersion()
      .then((version) => {
        setVersion(version);
      })
      .catch((err) => {
        console.warn('Failed to get app version:', err);
      });
  }, []);

  return (
    <Sidebar
      variant="sidebar"
      collapsible="none"
      className="border-border/40 border-r shadow-sm"
    >
      <SidebarHeader className="flex justify-center px-4 py-5">
        <div className="flex w-full items-center justify-center gap-2">
          <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
          <span className="text-lg font-bold">Model Manager</span>
        </div>
      </SidebarHeader>
      <SidebarContent className="py-2">
        <SidebarMenu className="space-y-2 px-3">
          {tabs.map((tab) => (
            <SidebarMenuItem key={tab.id}>
              <SidebarMenuButton
                isActive={activeTab === tab.id}
                onClick={() => onTabChange(tab.id)}
                className="cursor-pointer rounded-sm"
              >
                <div className="flex w-full items-center gap-3">
                  <tab.icon className="h-5 w-5" />
                  <span className="font-medium">{tab.label}</span>
                </div>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter className="border-border/40 mt-auto border-t py-4">
        <div className="text-muted-foreground space-y-1 px-4 text-xs">
          <div className="font-medium">PictoPy v{version}</div>
          <div>© {new Date().getFullYear()} PictoPy</div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
};
