import React from 'react';
import { Cloud, MoreHorizontal, Copy, X, FileImage } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';

type Props = {
  open: boolean;
  onClose: () => void;
  filePath?: string;
  fileName?: string;
  fileSize?: string | number;
};

const formatSize = (s?: string | number) => {
  // FIX: Check for null/undefined specifically so '0' is allowed as a valid size
  if (s === undefined || s === null || s === '') return '';
  
  const n = typeof s === 'string' ? Number(s) : s;
  if (Number.isNaN(n)) return String(s);
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
};

export const ShareOptionsModal: React.FC<Props> = ({
  open,
  onClose,
  filePath,
  fileName,
  fileSize
}) => {
  if (!open) return null;

  const copyPath = async () => {
    if (!filePath) {
      console.warn('No file path to copy');
      return;
    }
    try {
      await navigator.clipboard.writeText(filePath);
      console.log('File path copied:', filePath);
    } catch (err) {
      console.error('Failed to copy path:', err);
    }
  };

  const onShare = async () => {
    if (!filePath) {
      console.warn('No file path to share');
      return;
    }

    try {
      console.log('Starting OneDrive share flow for:', filePath);

      const shareUrl = await invoke<string>('onedrive_share', { path: filePath });
      console.log('Share link generated:', shareUrl);

      console.log('Opening native share for:', filePath);
      await invoke('share_file', { path: filePath });
      console.log('Native share dialog opened.');
    } catch (err) {
      console.error('OneDrive share failed:', err);
    }
  };

  const placeholderTileClick = (name: string) => {
    console.log(`Tile clicked: ${name}`, { filePath });
  };

  return (
    <div
      className="absolute top-20 left-5 z-50 w-[360px] max-w-full rounded-lg bg-black/80 p-3 text-white backdrop-blur-md shadow-lg"
      role="dialog"
      aria-modal="true"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold">More share options</h3>
          <p className="text-xs text-gray-300">
            Choose how you want to share this file
          </p>
        </div>
        <button
          aria-label="Close share options"
          onClick={onClose}
          className="rounded p-1 text-gray-300 hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* File info */}
      <div className="mt-3 flex items-center gap-3 rounded border border-white/10 bg-black/60 p-2">
        <div className="flex h-12 w-12 items-center justify-center rounded bg-white/5">
          <FileImage className="h-6 w-6 text-white/80" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium">
            {fileName ?? 'Unknown file'}
          </div>
          <div className="text-xs text-gray-400">{formatSize(fileSize)}</div>
        </div>
        <div>
          <button
            aria-label="Copy file path"
            onClick={copyPath}
            disabled={!filePath}
            className={`rounded bg-white/5 px-2 py-1 text-xs text-gray-200 ${
              filePath ? 'hover:bg-white/10' : 'cursor-not-allowed opacity-50'
            }`}
          >
            <Copy className="mr-2 inline h-4 w-4 align-middle" /> Copy
          </button>
        </div>
      </div>

      {/* Primary actions */}
      <div className="mt-3 flex gap-2">
        <button
          onClick={onShare}
          disabled={!filePath}
          className={`flex-1 inline-flex items-center gap-2 rounded border border-white/10 px-3 py-2 text-sm font-medium ${
            filePath ? 'hover:bg-white/5' : 'cursor-not-allowed opacity-50'
          }`}
        >
          <Cloud className="h-4 w-4" />
          <span>Using OneDrive</span>
        </button>

        <button
          onClick={onShare}
          disabled={!filePath} // FIX: Added disabled prop
          className={`inline-flex items-center gap-2 rounded border border-white/10 px-3 py-2 text-sm font-medium ${filePath ? 'hover:bg-white/5' : 'cursor-not-allowed opacity-50'}`}
          aria-label="Using more options"
        >
          <MoreHorizontal className="h-4 w-4" />
          <span>More options</span>
        </button>
      </div>

      <div className="my-3 h-px bg-white/10" />

      {/* Tiles grid */}
      <div className="grid grid-cols-3 gap-2">
        <button
          className={`flex flex-col items-center gap-1 rounded bg-white/5 p-3 text-xs ${
            filePath ? 'hover:bg-white/10' : 'cursor-not-allowed opacity-50'
          }`}
          onClick={copyPath}
          aria-label="Copy file"
          disabled={!filePath}
        >
          <Copy className="h-5 w-5" />
          <span>Copy file</span>
        </button>

        <button
          className="flex flex-col items-center gap-1 rounded bg-white/5 p-3 text-xs hover:bg-white/10"
          onClick={() => placeholderTileClick('Snip & Sketch')}
          aria-label="Snip and Sketch"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 7h18M3 12h18M3 17h18" />
          </svg>
          <span>Snip &amp; Sketch</span>
        </button>

        <button
          className="flex flex-col items-center gap-1 rounded bg-white/5 p-3 text-xs hover:bg-white/10"
          onClick={() => placeholderTileClick('OneNote')}
          aria-label="OneNote for Windows"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M4 3h16v18H4z" />
          </svg>
          <span>OneNote</span>
        </button>

        <button
          className="flex flex-col items-center gap-1 rounded bg-white/5 p-3 text-xs hover:bg-white/10"
          onClick={() => placeholderTileClick('Phone Link')}
          aria-label="Phone Link"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 7v10a2 2 0 0 0 2 2h10" />
          </svg>
          <span>Phone Link</span>
        </button>

        <button
          className="flex flex-col items-center gap-1 rounded bg-white/5 p-3 text-xs hover:bg-white/10"
          onClick={() => placeholderTileClick('Discord')}
          aria-label="Discord"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M8 12c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2" />
          </svg>
          <span>Discord</span>
        </button>

        <button
          className="flex flex-col items-center gap-1 rounded bg-white/5 p-3 text-xs hover:bg-white/10"
          onClick={() => placeholderTileClick('More apps')}
          aria-label="More apps"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="3" />
          </svg>
          <span>More</span>
        </button>
      </div>

      {/* Footer */}
      <div className="mt-3 text-xs text-gray-400">
        <div className="truncate">{filePath ?? 'Path not available'}</div>
      </div>
    </div>
  );
};

export default ShareOptionsModal;