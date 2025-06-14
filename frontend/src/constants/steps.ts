import { Step } from '@/types/steps';
import { UpdateStep } from '@/components/Steps/UpdateStep';
import { FolderSetupStep } from '@/components/Steps/FolderSetupStep';
export const STEPS: Step[] = [
  {
    id: 'update',
    component: UpdateStep,
  },
  {
    id: 'folderSetup',
    component: FolderSetupStep,
  },
];
