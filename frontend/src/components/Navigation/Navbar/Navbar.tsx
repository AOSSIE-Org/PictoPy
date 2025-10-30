import { Input } from '@/components/ui/input';
import { ThemeSelector } from '@/components/ThemeToggle';
import { Search } from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { clearSearch } from '@/features/searchSlice';
import { convertFileSrc } from '@tauri-apps/api/core';
import { FaceSearchDialog } from '@/components/Dialog/FaceSearchDialog';

export function Navbar() {
  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);

  const searchState = useSelector((state: any) => state.search);
  const isSearchActive = searchState.active;
  const queryImage = searchState.queryImage;

  const dispatch = useDispatch();
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
          {/* Query Image */}
          {queryImage && (
            <div className="relative mr-2 ml-2">
              <img
                src={
                  queryImage?.startsWith('data:')
                    ? queryImage
                    : convertFileSrc(queryImage)
                }
                alt="Query"
                className="h-7 w-7 rounded object-cover"
              />
              {isSearchActive && (
                <button
                  onClick={() => dispatch(clearSearch())}
                  className="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-600 text-[10px] leading-none text-white"
                  title="Close"
                  aria-label="Close"
                >
                  ✕
                </button>
              )}
            </div>
          )}

          {/* Input */}
          <Input
            type="search"
            placeholder="Add to your search"
            className="mr-2 flex-1 border-0 bg-neutral-200"
          />

          {/* FaceSearch Dialog */}

          <FaceSearchDialog />

          <button
            className="text-muted-foreground hover:bg-accent dark:hover:bg-accent/50 hover:text-foreground mx-1 cursor-pointer rounded-sm p-2"
            title="Search"
            aria-label="Search"
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
