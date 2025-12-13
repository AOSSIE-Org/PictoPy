import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { Folder } from 'lucide-react';
import { useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import FolderPicker from '@/components/FolderPicker/FolderPicker';
import { useFolderOperations } from '@/hooks/useFolderOperations';
import { useBulkFolderSelection } from '@/hooks/useBulkFolderSelection';
import SettingsCard from './SettingsCard';
import {
  FolderProgressSummary,
  FolderBulkActions,
  FolderSection,
} from '@/components/FolderManagement';
import {
  mergeFoldersWithStatus,
  groupFoldersByStatus,
  calculateFolderStats,
  loadFolderPreferences,
  saveFolderPreferences,
  FolderPreferences,
  FolderWithStatus,
} from '@/utils/folderUtils';

/**
 * Component for managing folder operations in settings
 * Supports bulk AI tagging, progress tracking, and smart sorting
 */
const FolderManagementCard: React.FC = () => {
  const {
    folders,
    toggleAITagging,
    deleteFolder,
    bulkEnableAITagging,
    bulkDisableAITagging,
    enableAITaggingPending,
    disableAITaggingPending,
    deleteFolderPending,
    bulkEnablePending,
    bulkDisablePending,
  } = useFolderOperations();

  const taggingStatus = useSelector(
    (state: RootState) => state.folders.taggingStatus,
  );

  // Selection state
  const {
    selectedIds,
    toggleSelection,
    selectAll,
    deselectAll,
    selectedCount,
    isAllSelected,
    getSelectedFolders,
  } = useBulkFolderSelection();

  // Collapsed sections state (persisted)
  const [preferences, setPreferences] = useState<FolderPreferences>(
    loadFolderPreferences,
  );

  // Save preferences when they change
  useEffect(() => {
    saveFolderPreferences(preferences);
  }, [preferences]);

  // Merge folders with their tagging status
  const foldersWithStatus: FolderWithStatus[] = useMemo(
    () => mergeFoldersWithStatus(folders, taggingStatus),
    [folders, taggingStatus],
  );

  // Group folders by status
  const groupedFolders = useMemo(
    () => groupFoldersByStatus(foldersWithStatus),
    [foldersWithStatus],
  );

  // Calculate statistics
  const stats = useMemo(
    () => calculateFolderStats(groupedFolders),
    [groupedFolders],
  );

  // Toggle section collapse
  const toggleSectionCollapse = useCallback(
    (section: 'completed' | 'inProgress' | 'pending') => {
      setPreferences((prev) => ({
        ...prev,
        collapsedSections: {
          ...prev.collapsedSections,
          [section]: !prev.collapsedSections[section],
        },
      }));
    },
    [],
  );

  // Bulk action handlers
  const handleSelectAll = useCallback(() => {
    selectAll(foldersWithStatus);
  }, [selectAll, foldersWithStatus]);

  const handleEnableAll = useCallback(() => {
    const pendingFolderIds = groupedFolders.pending.map((f) => f.folder_id);
    bulkEnableAITagging(pendingFolderIds);
  }, [groupedFolders.pending, bulkEnableAITagging]);

  const handleEnableSelected = useCallback(() => {
    const selectedFolders = getSelectedFolders(foldersWithStatus);
    const pendingSelectedIds = selectedFolders
      .filter((f) => !f.AI_Tagging)
      .map((f) => f.folder_id);
    if (pendingSelectedIds.length > 0) {
      bulkEnableAITagging(pendingSelectedIds);
    } else {
      // If all selected already have AI tagging, enable anyway (re-trigger)
      bulkEnableAITagging(selectedFolders.map((f) => f.folder_id));
    }
  }, [getSelectedFolders, foldersWithStatus, bulkEnableAITagging]);

  const handleDisableAll = useCallback(() => {
    const enabledFolderIds = [
      ...groupedFolders.completed,
      ...groupedFolders.inProgress,
    ].map((f) => f.folder_id);
    bulkDisableAITagging(enabledFolderIds);
  }, [groupedFolders, bulkDisableAITagging]);

  const handleDisableSelected = useCallback(() => {
    const selectedFolders = getSelectedFolders(foldersWithStatus);
    const enabledSelectedIds = selectedFolders
      .filter((f) => f.AI_Tagging)
      .map((f) => f.folder_id);
    bulkDisableAITagging(enabledSelectedIds);
  }, [getSelectedFolders, foldersWithStatus, bulkDisableAITagging]);

  const isTaggingPending =
    enableAITaggingPending ||
    disableAITaggingPending ||
    bulkEnablePending ||
    bulkDisablePending;

  return (
    <SettingsCard
      icon={Folder}
      title="Folder Management"
      description="Configure your photo library folders and AI settings"
    >
      {folders.length > 0 ? (
        <>
          {/* Progress Summary */}
          <FolderProgressSummary stats={stats} />

          {/* Bulk Actions */}
          <FolderBulkActions
            totalCount={stats.total}
            selectedCount={selectedCount}
            pendingCount={stats.pending}
            enabledCount={stats.completed + stats.inProgress}
            isAllSelected={isAllSelected(foldersWithStatus)}
            onSelectAll={handleSelectAll}
            onDeselectAll={deselectAll}
            onEnableAll={handleEnableAll}
            onEnableSelected={handleEnableSelected}
            onDisableAll={handleDisableAll}
            onDisableSelected={handleDisableSelected}
            isEnabling={bulkEnablePending || enableAITaggingPending}
            isDisabling={bulkDisablePending || disableAITaggingPending}
          />

          {/* Folder Sections */}
          <div className="space-y-2">
            <FolderSection
              type="inProgress"
              folders={groupedFolders.inProgress}
              isCollapsed={preferences.collapsedSections.inProgress}
              onToggleCollapse={() => toggleSectionCollapse('inProgress')}
              selectedIds={selectedIds}
              onToggleSelection={toggleSelection}
              onToggleAITagging={toggleAITagging}
              onDeleteFolder={deleteFolder}
              isTaggingPending={isTaggingPending}
              isDeletePending={deleteFolderPending}
            />

            <FolderSection
              type="pending"
              folders={groupedFolders.pending}
              isCollapsed={preferences.collapsedSections.pending}
              onToggleCollapse={() => toggleSectionCollapse('pending')}
              selectedIds={selectedIds}
              onToggleSelection={toggleSelection}
              onToggleAITagging={toggleAITagging}
              onDeleteFolder={deleteFolder}
              isTaggingPending={isTaggingPending}
              isDeletePending={deleteFolderPending}
            />

            <FolderSection
              type="completed"
              folders={groupedFolders.completed}
              isCollapsed={preferences.collapsedSections.completed}
              onToggleCollapse={() => toggleSectionCollapse('completed')}
              selectedIds={selectedIds}
              onToggleSelection={toggleSelection}
              onToggleAITagging={toggleAITagging}
              onDeleteFolder={deleteFolder}
              isTaggingPending={isTaggingPending}
              isDeletePending={deleteFolderPending}
            />
          </div>
        </>
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
