import React, { useEffect, useMemo, useState } from 'react';
import { Folder, Trash2, Check } from 'lucide-react';

import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';

import { useFolderOperations } from '@/hooks/useFolderOperations';
import { FolderDetails } from '@/types/Folder';
import SettingsCard from './SettingsCard';

/**
 * Component for managing folder operations in settings
 */
const FolderManagementCard: React.FC = () => {
  const {
    folders,
    toggleAITagging,
    deleteFolder,
    enableAITaggingPending,
    disableAITaggingPending,
    deleteFolderPending,
    bulkEnableAITagging,
    bulkDisableAITagging,
    bulkPending,
  } = useFolderOperations();

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  // Selection state
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  // const allFolderIds = useMemo(() => folders.map((f) => f.folder_id), [folders]);

  // Collapse state persisted in localStorage
  const [collapsed, setCollapsed] = useState<{
    completed: boolean;
    inProgress: boolean;
    pending: boolean;
  }>(() => {
    try {
      const raw = localStorage.getItem('folder-sections-collapsed');
      return (
        (raw && JSON.parse(raw)) || {
          completed: false,
          inProgress: false,
          pending: false,
        }
      );
    } catch {
      return { completed: false, inProgress: false, pending: false };
    }
  });

  useEffect(() => {
    localStorage.setItem('folder-sections-collapsed', JSON.stringify(collapsed));
  }, [collapsed]);

  // Derived grouping and stats
  const { completed, inProgress, pending, stats } = useMemo(() => {
    const completed: FolderDetails[] = [];
    const inProgress: FolderDetails[] = [];
    const pending: FolderDetails[] = [];

    folders.forEach((folder) => {
      const status = taggingStatus[folder.folder_id];
      const pct = Math.round(status?.tagging_percentage ?? 0);
      if (pct >= 100 || folder.taggingCompleted) {
        completed.push(folder);
      } else if (folder.AI_Tagging && pct > 0 && pct < 100) {
        inProgress.push(folder);
      } else {
        pending.push(folder);
      }
    });

    const stats = {
      total: folders.length,
      completed: completed.length,
      inProgress: inProgress.length,
      pending: pending.length,
    };

    return { completed, inProgress, pending, stats };
  }, [folders, taggingStatus]);

  const progressPct = useMemo(() => {
    if (stats.total === 0) return 0;
    return Math.round((stats.completed / stats.total) * 100);
  }, [stats.total, stats.completed]);

  // Selection helpers
  const isSelected = (id: string) => !!selected[id];
  const toggleSelect = (id: string) =>
    setSelected((s) => ({ ...s, [id]: !s[id] }));
  const clearSelection = () => setSelected({});
  const selectedIds = useMemo(
    () => Object.entries(selected).filter(([, v]) => v).map(([k]) => k),
    [selected],
  );

  const selectAllVisible = (ids: string[], checked: boolean) => {
    setSelected((s) => {
      const next = { ...s };
      ids.forEach((id) => (next[id] = checked));
      return next;
    });
  };

  // Bulk actions
  const handleTagAll = async () => {
    // Preserve user intent: only enable for folders that are not already enabled/completed
    const toEnable = pending.map((f) => f.folder_id);
    if (toEnable.length === 0) return;
    await bulkEnableAITagging(toEnable);
  };

  const handleTagSelected = async () => {
    if (selectedIds.length === 0) return;
    await bulkEnableAITagging(selectedIds);
    clearSelection();
  };

  const handleDisableSelected = async () => {
    if (selectedIds.length === 0) return;
    await bulkDisableAITagging(selectedIds);
    clearSelection();
  };

  const anyMutationPending =
    enableAITaggingPending || disableAITaggingPending || deleteFolderPending || bulkPending;

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {/* Progress Summary */}
      <div className="mb-4 rounded-md border border-border p-4">
        <div className="mb-2 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            AI Tagging Progress: {stats.completed}/{stats.total} folders tagged ({progressPct}%)
          </div>
          <div className="flex gap-3 text-sm">
            <span className="text-green-600 dark:text-green-400">Completed: {stats.completed}</span>
            <span className="text-blue-600 dark:text-blue-400">In Progress: {stats.inProgress}</span>
            <span className="text-amber-700 dark:text-amber-400">Pending: {stats.pending}</span>
          </div>
        </div>
        <Progress value={progressPct} indicatorClassName={progressPct >= 100 ? 'bg-green-500' : 'bg-blue-500'} />
      </div>

      {/* Bulk Controls */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Button size="sm" onClick={handleTagAll} disabled={anyMutationPending || stats.pending === 0}>
          AI Tag All
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => selectAllVisible([...completed, ...inProgress, ...pending].map((f) => f.folder_id), true)}
          disabled={anyMutationPending || folders.length === 0}
        >
          Select All
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={clearSelection}
          disabled={anyMutationPending || selectedIds.length === 0}
        >
          Clear Selection
        </Button>
        <Button
          size="sm"
          variant="default"
          onClick={handleTagSelected}
          disabled={anyMutationPending || selectedIds.length === 0}
        >
          Tag Selected
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={handleDisableSelected}
          disabled={anyMutationPending || selectedIds.length === 0}
        >
          Disable AI for Selected
        </Button>
      </div>

      {folders.length > 0 ? (
        <div className="space-y-4">
          {/* Completed Section */}
          <Section
            title={`Completed (${completed.length})`}
            collapsed={collapsed.completed}
            onToggle={() => setCollapsed((c) => ({ ...c, completed: !c.completed }))}
          >
            {completed.map((folder: FolderDetails) => (
              <FolderRow
                key={folder.folder_id}
                folder={folder}
                pct={Math.round(taggingStatus[folder.folder_id]?.tagging_percentage ?? 100)}
                checked={isSelected(folder.folder_id)}
                onCheckedChange={() => toggleSelect(folder.folder_id)}
                toggleAITagging={() => toggleAITagging(folder)}
                deleteFolder={() => deleteFolder(folder.folder_id)}
                disableAll={anyMutationPending}
              />
            ))}
          </Section>

          {/* In Progress Section */}
          <Section
            title={`In Progress (${inProgress.length})`}
            collapsed={collapsed.inProgress}
            onToggle={() => setCollapsed((c) => ({ ...c, inProgress: !c.inProgress }))}
          >
            {inProgress.map((folder: FolderDetails) => (
              <FolderRow
                key={folder.folder_id}
                folder={folder}
                pct={Math.round(taggingStatus[folder.folder_id]?.tagging_percentage ?? 0)}
                checked={isSelected(folder.folder_id)}
                onCheckedChange={() => toggleSelect(folder.folder_id)}
                toggleAITagging={() => toggleAITagging(folder)}
                deleteFolder={() => deleteFolder(folder.folder_id)}
                disableAll={anyMutationPending}
              />
            ))}
          </Section>

          {/* Pending Section */}
          <Section
            title={`Pending (${pending.length})`}
            collapsed={collapsed.pending}
            onToggle={() => setCollapsed((c) => ({ ...c, pending: !c.pending }))}
          >
            <div className="mb-2 flex items-center gap-2">
              <input
                type="checkbox"
                className="h-4 w-4 cursor-pointer accent-blue-600"
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  selectAllVisible(
                    pending.map((f) => f.folder_id),
                    e.currentTarget.checked,
                  )
                }
              />
              <span className="text-sm text-muted-foreground">Select all pending</span>
            </div>
            {pending.map((folder: FolderDetails) => (
              <FolderRow
                key={folder.folder_id}
                folder={folder}
                pct={Math.round(taggingStatus[folder.folder_id]?.tagging_percentage ?? 0)}
                checked={isSelected(folder.folder_id)}
                onCheckedChange={() => toggleSelect(folder.folder_id)}
                toggleAITagging={() => toggleAITagging(folder)}
                deleteFolder={() => deleteFolder(folder.folder_id)}
                disableAll={anyMutationPending}
              />
            ))}
          </Section>
        </div>
      ) : (
        <div className="py-8 text-center">
          <Folder className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <h3 className="text-foreground mb-1 text-lg font-medium">
            No folders configured
          </h3>
          <p className="text-muted-foreground text-sm">
            Add your first photo library folder to get started
          </p>
        </div>
      )}

      <div className="border-border mt-6 border-t pt-6">
        <FolderPicker />
      </div>
    </SettingsCard>
  );
};

export default FolderManagementCard;

// Helper components
const Section: React.FC<{
  title: string;
  collapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}> = ({ title, collapsed, onToggle, children }) => {
  return (
    <div className="border-border overflow-hidden rounded-md border">
      <button
        type="button"
        className="flex w-full items-center justify-between bg-muted/40 px-4 py-2 text-left text-sm"
        onClick={onToggle}
      >
        <span>{title}</span>
        <span className="text-muted-foreground">{collapsed ? 'Show' : 'Hide'}</span>
      </button>
      {!collapsed && <div className="divide-y divide-border">{children}</div>}
    </div>
  );
};

const FolderRow: React.FC<{
  folder: FolderDetails;
  pct: number;
  checked: boolean;
  onCheckedChange: () => void;
  toggleAITagging: () => void;
  deleteFolder: () => void;
  disableAll: boolean;
}> = ({
  folder,
  pct,
  checked,
  onCheckedChange,
  toggleAITagging,
  deleteFolder,
  disableAll,
}) => {
  return (
    <div className="group bg-background/50 relative flex items-start justify-between p-4 transition-all hover:bg-muted/20">
      <div className="flex flex-1 items-start gap-3">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 cursor-pointer accent-blue-600"
          checked={checked}
          onChange={onCheckedChange}
          disabled={disableAll}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <Folder className="h-4 w-4 flex-shrink-0 text-gray-500 dark:text-gray-400" />
            <span className="text-foreground truncate">{folder.folder_path}</span>
          </div>
          {folder.AI_Tagging && (
            <div className="mt-3">
              <div className="text-muted-foreground mb-1 flex items-center justify-between text-xs">
                <span>AI Tagging Progress</span>
                <span
                  className={pct >= 100 ? 'flex items-center gap-1 text-green-500' : 'text-muted-foreground'}
                >
                  {pct >= 100 && <Check className="h-3 w-3" />}
                  {pct}%
                </span>
              </div>
              <Progress value={pct} indicatorClassName={pct >= 100 ? 'bg-green-500' : 'bg-blue-500'} />
            </div>
          )}
        </div>
      </div>

      <div className="ml-4 flex items-center gap-4">
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-sm">AI Tagging</span>
          <Switch
            className="cursor-pointer"
            checked={folder.AI_Tagging}
            onCheckedChange={toggleAITagging}
            disabled={disableAll}
          />
        </div>

        <Button
          onClick={deleteFolder}
          variant="outline"
          size="sm"
          className="h-8 w-8 cursor-pointer text-gray-500 hover:border-red-300 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
          disabled={disableAll}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
