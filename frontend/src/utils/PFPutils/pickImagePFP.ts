import { open } from '@tauri-apps/plugin-dialog';
import { readFile } from '@tauri-apps/plugin-fs';

const EXTENSION_TO_MIME: Record<string, string> = {
  png: 'image/png',
  webp: 'image/webp',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
};

// A data URL rather than a path, because the crop step reads the canvas back
// with toDataURL and a cross-origin asset:// source would taint it. Null means
// the user cancelled.
export async function pickImageFile(): Promise<string | null> {
  const selected = await open({
    multiple: false,
    title: 'Select a profile picture',
    filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp'] }],
  });

  if (!selected || Array.isArray(selected)) {
    return null;
  }

  const bytes = await readFile(selected);
  const extension = selected.split('.').pop()?.toLowerCase() ?? '';
  const mime = EXTENSION_TO_MIME[extension] ?? 'image/jpeg';

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(new Blob([bytes], { type: mime }));
  });
}
