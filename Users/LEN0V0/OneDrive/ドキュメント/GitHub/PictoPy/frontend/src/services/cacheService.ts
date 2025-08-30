import { invoke } from '@tauri-apps/api/core';

export async function deleteCache() {
  try {
    const result = await invoke('delete_cache');
    return result;
  } catch (error) {
    console.error('Error deleting cache:', error);
    throw error;
  }
}
