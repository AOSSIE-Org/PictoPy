import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { startTextSearch, clearSearch } from '@/features/searchSlice';

import { Input } from '@/components/ui/input';
import { ThemeSelector } from '@/components/ThemeToggle';
import { Search } from 'lucide-react';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { convertFileSrc } from '@tauri-apps/api/core';
import { FaceSearchDialog } from '@/components/Dialog/FaceSearchDialog';
import { useRef } from 'react';

export function Navbar() {
  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);
  const queryImage = useSelector((state: any) => state.search.queryImage);
  const dispatch = useDispatch();
  const [searchInput, setSearchInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounce search
  useEffect(() => {
    const trimmed = searchInput.trim();

    const timer = setTimeout(() => {
      if (trimmed) {
        dispatch(startTextSearch(trimmed));
      } else {
        dispatch(clearSearch());
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchInput, dispatch]);

  return (
    <div className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b pr-4 backdrop-blur">
      {/* Logo */}
      <div className="flex w-[256px] items-center justify-center">
        <a href="/" className="flex items-center space-x-2">
          <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
          <span className="text-xl font-bold">PictoPy</span>
        </a>
      </div>

      {/* Search Bar */}
      <div className="mx-auto flex max-w-md flex-1 justify-center px-4">
        <div className="dark:bg-muted/50 flex w-full items-center gap-1 rounded-md bg-neutral-100 px-1 py-1">
          {/* Query Image Preview */}
          {queryImage && (
            <div className="relative mr-2 ml-2">
              <img
                src={
                  queryImage.startsWith('data:')
                    ? queryImage
                    : convertFileSrc(queryImage)
                }
                alt="Query"
                className="h-7 w-7 rounded object-cover"
              />
            </div>
          )}

          {/* Search Input */}
          <Input
            ref={inputRef}
            type="search"
            placeholder="Search by tags, faces, or location..."
            className="mr-2 flex-1 border-0 bg-neutral-200"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                setSearchInput('');
                dispatch(clearSearch());
              }
            }}
          />

          {/* Face Search */}
          <FaceSearchDialog />

          {/* Search Icon */}
          <button
            onClick={() => inputRef.current?.focus()}
            className="text-muted-foreground hover:bg-accent dark:hover:bg-accent/50 hover:text-foreground mx-1 rounded-sm p-2"
            title="Focus search"
          >
            <Search className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Right Side */}
      <div className="flex items-center space-x-4">
        <ThemeSelector />
        <div className="flex items-center space-x-2">
          <span className="hidden text-sm sm:inline-block">
            Welcome <span className="text-muted-foreground">{userName}</span>
          </span>
          <a href="/settings" className="p-2">
            <img
              src={userAvatar || '/photo1.png'}
              className="hover:ring-primary/50 h-8 w-8 cursor-pointer rounded-full transition-all hover:ring-2"
              alt="User avatar"
            />
          </a>
        </div>
      </div>
    </div>
  );
}
