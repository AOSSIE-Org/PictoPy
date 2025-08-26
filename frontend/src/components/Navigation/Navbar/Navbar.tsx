import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { ThemeSelector } from '@/components/ThemeToggle';
import {
  Bell,
  Search,
  User,
  Upload,
  Camera,
  Scan,
  X,
  ScanFace,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from '@/components/ui/dialog';

export function Navbar() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  let savedData = JSON.parse(
    localStorage.getItem('pictopy-user-data') || '{"name":"Guest"}',
  );

  return (
    <div className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b pr-4 backdrop-blur">
      <div className="flex w-[256px] items-center justify-center">
        <a href="/" className="flex items-center space-x-2">
          <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
          <span className="text-xl font-bold">PictoPy</span>
        </a>
      </div>

      <div className="mx-auto flex max-w-md flex-1 justify-center px-4">
        <div className="relative w-full">
          <Search className="text-muted-foreground absolute top-2.5 left-2.5 h-4 w-4" />
          <Input
            type="search"
            placeholder="Search images..."
            className="bg-muted/50 w-full pr-10 pl-8"
          />

          {/* Face Detection Trigger Button */}
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="absolute top-0.5 right-1 h-8 w-8 p-1"
              >
                <ScanFace className="text-muted-foreground h-4 w-4" />
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
                  onClick={() => {}}
                  disabled={false}
                  className="flex h-32 flex-col items-center justify-center gap-2 p-0"
                  variant="outline"
                >
                  {false ? (
                    <>
                      <span className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
                      <span className="text-center text-xs">Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="text-muted-foreground mb-1 h-8 w-8" />
                      <span className="text-sm font-medium">Upload Photo</span>
                      <span className="text-muted-foreground text-center text-xs">
                        Browse your computer
                      </span>
                    </>
                  )}
                </Button>

                <Button
                  onClick={() => {}}
                  disabled={false}
                  className="flex h-32 flex-col items-center justify-center gap-2 p-0"
                  variant="outline"
                >
                  {false ? (
                    <>
                      <span className="h-5 w-5 animate-pulse rounded-full bg-red-500"></span>
                      <span className="text-center text-xs">Capturing...</span>
                    </>
                  ) : (
                    <>
                      <Camera className="text-muted-foreground mb-1 h-8 w-8" />
                      <span className="text-sm font-medium">Use Webcam</span>
                      <span className="text-muted-foreground text-center text-xs">
                        Capture with camera
                      </span>
                    </>
                  )}
                </Button>
              </div>

              <p className="text-muted-foreground mt-2 text-xs">
                PictoPy will analyze the face and find matching images in your
                gallery.
              </p>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="bg-brand-orange absolute top-1 right-1 h-2 w-2 rounded-full" />
          <span className="sr-only">Notifications</span>
        </Button>
        <ThemeSelector />
        <div className="flex items-center space-x-2">
          <span className="hidden text-sm sm:inline-block">
            Welcome <span className="text-muted-foreground">Rahul</span>
          </span>
          <a href="/settings" className="p-2">
            <img
              src={savedData.avatarUrl || '/photo1.png'}
              className="hover:ring-primary/50 h-8 w-8 cursor-pointer rounded-full transition-all hover:ring-2"
              alt="User avatar"
            />
          </a>
        </div>
      </div>
    </div>
  );
}
