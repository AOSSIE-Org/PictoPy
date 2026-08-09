import { open } from '@tauri-apps/plugin-dialog';
import { readFile } from '@tauri-apps/plugin-fs';

const EXTENSION_TO_MIME: Record<string, string> = {
  png: 'image/png',
  webp: 'image/webp',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
};

// Resolves a data URL rather than the path: react-easy-crop and canvas both
// need something an <img> can load, and a Tauri file path is not that. Null
// means the user cancelled.
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
