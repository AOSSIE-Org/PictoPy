import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { ThemeSelector } from '@/components/ThemeToggle';
import { Bell, Search, Upload, Camera, ScanFace } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useDispatch, useSelector } from 'react-redux';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { useFile } from '@/hooks/selectFile';
import { clearSearch, setResults, startSearch } from '@/features/searchSlice';
import { convertFileSrc } from '@tauri-apps/api/core';
import type { Image } from '@/types/Media';

export function Navbar() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);

  // Move all useSelector calls to the top level
  const searchState = useSelector((state: any) => state.search);
  const isSearchActive = searchState.active;
  const queryImage = searchState.queryImage;

  const { pickSingleFile } = useFile({ title: 'Select File' });

  const dispatch = useDispatch();
  const handlePickFile = async () => {
    const file = await pickSingleFile();
    if (file) {
      dispatch(startSearch(file.path));
      const result = file.result.data as unknown as Image[];
      dispatch(setResults(result));
      setIsDialogOpen(false);
    }
  };

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
        <div className="bg-muted/50 flex w-full items-center rounded-md pr-2">
          {/* Query Image */}
          {queryImage && (
            <div className="relative mr-2 ml-2">
              <img
                src={convertFileSrc(queryImage) || 'photo.png'}
                alt="Query"
                className="h-7 w-7 rounded object-cover"
              />
              {isSearchActive && (
                <button
                  onClick={() => dispatch(clearSearch())}
                  className="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-600 text-[10px] leading-none text-white"
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
            className="flex-1 border-0 bg-transparent focus:ring-0"
          />

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 p-1">
                <ScanFace className="h-4 w-4" />
                <span className="sr-only">Face Detection Search</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Face Detection Search</DialogTitle>
                <DialogDescription>
                  Search for images containing specific faces by uploading a
                  photo or using your webcam.
                </DialogDescription>
              </DialogHeader>

              <div className="grid grid-cols-2 gap-4 py-4">
                <Button
                  onClick={handlePickFile}
                  disabled={false}
                  className="flex h-32 flex-col items-center justify-center gap-2 p-0"
                  variant="outline"
                >
                  <Upload className="text-muted-foreground mb-1 h-8 w-8" />
                  <span className="text-sm font-medium">Upload Photo</span>
                  <span className="text-muted-foreground text-center text-xs">
                    Browse your computer
                  </span>
                </Button>

                <Button
                  onClick={() => {}}
                  disabled={false}
                  className="flex h-32 flex-col items-center justify-center gap-2 p-0"
                  variant="outline"
                >
                  <Camera className="text-muted-foreground mb-1 h-8 w-8" />
                  <span className="text-sm font-medium">Use Webcam</span>
                  <span className="text-muted-foreground text-center text-xs">
                    Capture with camera
                  </span>
                </Button>
              </div>

              <p className="text-muted-foreground mt-2 text-xs">
                PictoPy will analyze the face and find matching images in your
                gallery.
              </p>
            </DialogContent>
          </Dialog>

          <button className="text-muted-foreground mx-1 hover:text-white">
            <Search className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Right Side */}
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="bg-brand-orange absolute top-1 right-1 h-2 w-2 rounded-full" />
          <span className="sr-only">Notifications</span>
        </Button>
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
