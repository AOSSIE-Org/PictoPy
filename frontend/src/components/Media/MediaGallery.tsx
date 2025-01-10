import { useMemo, useState, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import MediaGrid from './Mediagrid';
import MediaView from './MediaView';
import SortingControls from './SortningControls';
import PaginationControls from '../ui/PaginationControls';
import { MediaGalleryProps } from '@/types/Media';
import { sortMedia } from '@/utils/Media';

export default function MediaGallery({ mediaItems, title, type }: MediaGalleryProps) {
  const currentYear = new Date().getFullYear().toString();
  const [sortBy, setSortBy] = useState<string>('date');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);
  const [selectedImages, setSelectedImages] = useState<Set<number>>(new Set());
  const [showCollageDialog, setShowCollageDialog] = useState<boolean>(false);
  const [collageLayout, setCollageLayout] = useState<string>('grid');

  const itemsPerPage: number = 20;
  const itemsPerRow: number = 3;

  const sortedMedia = useMemo(() => sortMedia(mediaItems, [sortBy]), [mediaItems, sortBy]);
  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * itemsPerPage;
    return sortedMedia.slice(indexOfLastItem - itemsPerPage, indexOfLastItem);
  }, [sortedMedia, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(sortedMedia.length / itemsPerPage);

  const toggleImageSelection = useCallback((index: number) => {
    setSelectedImages((prev) => {
      const newSet = new Set(prev);
      newSet.has(index) ? newSet.delete(index) : newSet.add(index);
      return newSet;
    });
  }, []);

  const createCollage = useCallback(async () => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const selectedMediaItems = Array.from(selectedImages).map((index) => sortedMedia[index]);
    const images = await Promise.all(
      selectedMediaItems.map((item) => {
        return new Promise<HTMLImageElement>((resolve) => {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.src = item.url;
          img.onload = () => resolve(img);
        });
      })
    );

    let canvasWidth = 1920, canvasHeight = 1080;
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    if (collageLayout === 'grid') {
      const cols = Math.ceil(Math.sqrt(images.length));
      const rows = Math.ceil(images.length / cols);
      images.forEach((img, i) => {
        ctx.drawImage(img, (i % cols) * (canvasWidth / cols), Math.floor(i / cols) * (canvasHeight / rows), canvasWidth / cols, canvasHeight / rows);
      });
    } else if (collageLayout === 'horizontal') {
      images.forEach((img, i) => ctx.drawImage(img, i * (canvasWidth / images.length), 0, canvasWidth / images.length, canvasHeight));
    } else if (collageLayout === 'vertical') {
      images.forEach((img, i) => ctx.drawImage(img, 0, i * (canvasHeight / images.length), canvasWidth, canvasHeight / images.length));
    }

    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'collage.png';
      a.click();
      URL.revokeObjectURL(url);
    }, 'image/png');

    setShowCollageDialog(false);
    setSelectedImages(new Set());
  }, [selectedImages, sortedMedia, collageLayout]);

  return (
    <div className="w-full">
      <div className="mx-auto px-2 pb-8 pt-1 dark:bg-background dark:text-foreground">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-2xl font-bold">{title || currentYear}</h1>
          <SortingControls sortBy={sortBy} setSortBy={setSortBy} mediaItems={mediaItems} />
          {selectedImages.size > 0 && (
            <Button onClick={() => setShowCollageDialog(true)}>Create Collage ({selectedImages.size})</Button>
          )}
        </div>

        <MediaGrid mediaItems={currentItems} itemsPerRow={itemsPerRow} openMediaViewer={(index) => { setSelectedMediaIndex(index); setShowMediaViewer(true); }} type={type} selectedImages={selectedImages} onImageSelect={toggleImageSelection} />
        {totalPages >= 1 && <PaginationControls currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />}

        {showMediaViewer && <MediaView initialIndex={selectedMediaIndex} onClose={() => setShowMediaViewer(false)} allMedia={sortedMedia.map((item) => ({ url: item.url, path: item?.imagePath }))} currentPage={currentPage} itemsPerPage={itemsPerPage} type={type} />}

        <Dialog open={showCollageDialog} onOpenChange={setShowCollageDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Collage</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="flex flex-col gap-2">
                <span className="font-medium">Layout</span>
                <div className="flex gap-2">
                  <Button variant={collageLayout === 'grid' ? 'default' : 'outline'} onClick={() => setCollageLayout('grid')}>Grid</Button>
                  <Button variant={collageLayout === 'horizontal' ? 'default' : 'outline'} onClick={() => setCollageLayout('horizontal')}>Horizontal</Button>
                  <Button variant={collageLayout === 'vertical' ? 'default' : 'outline'} onClick={() => setCollageLayout('vertical')}>Vertical</Button>
                </div>
              </div>
              <Button onClick={createCollage}>Create Collage</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}