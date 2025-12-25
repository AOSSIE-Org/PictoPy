import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchAllVideos, scanVideos } from '@/api/api-functions';
import { APIResponse } from '@/types/API';
import { Video } from '@/types/Media';
import { VideoCard } from '@/components/Media/VideoCard';
import PlyrPlayer from '@/components/VideoPlayer/PlyrPlayer';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Calendar, ArrowDownAZ, RefreshCw } from 'lucide-react';
import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import { convertFileSrc } from '@tauri-apps/api/core';

const Videos: React.FC = () => {
  const { data, isLoading, refetch } = useQuery<APIResponse>({
    queryKey: ['videos'],
    queryFn: fetchAllVideos,
  });
  const [videos, setVideos] = useState<Video[]>([]);
  const [active, setActive] = useState<Video | null>(null);
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'name_asc'>(
    'date_desc',
  );

  useEffect(() => {
    const run = async () => {
      if (data?.success && Array.isArray(data.data)) {
        const list = data.data as unknown as Video[];
        setVideos(list);
        if (list.length === 0) {
          try {
            const scanned = await scanVideos();
            if (scanned?.success && Array.isArray(scanned.data)) {
              setVideos(scanned.data as unknown as Video[]);
            }
          } catch (error) {
            console.error('Failed to scan videos:', error);
            // Videos will remain empty, showing "No videos found" message
          }
        }
      }
    };
    run();
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <LoadingScreen />
      </div>
    );
  }

  // derived sorted list
  const sorted = [...videos].sort((a, b) => {
    if (sortBy === 'name_asc') {
      const an = (a.metadata?.name || '').toLowerCase();
      const bn = (b.metadata?.name || '').toLowerCase();
      return an.localeCompare(bn);
    }
    const ad = new Date(a.metadata?.date_created || 0).getTime();
    const bd = new Date(b.metadata?.date_created || 0).getTime();
    return sortBy === 'date_desc' ? bd - ad : ad - bd;
  });

  return (
    <div className="flex h-full w-full flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Videos</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="gap-2">
                <ArrowDownAZ className="h-4 w-4" /> Sort by
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() => setSortBy('date_desc')}
              >
                <Calendar className="h-4 w-4" /> Date (Newest)
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() => setSortBy('date_asc')}
              >
                <Calendar className="h-4 w-4" /> Date (Oldest)
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() => setSortBy('name_asc')}
              >
                <ArrowDownAZ className="h-4 w-4" /> Name (A–Z)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="text-muted-foreground flex flex-1 items-center justify-center">
          No videos found.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {sorted.map((v) => (
            <VideoCard key={v.id} video={v} onClick={() => setActive(v)} />
          ))}
        </div>
      )}

      {active && (
        // Animated modal
        <div className="fixed inset-0 z-50 grid place-items-center p-4">
          <div
            className="animate-in fade-in absolute inset-0 cursor-pointer bg-black/80 duration-200"
            onClick={() => setActive(null)}
            aria-label="Close video overlay"
          />
          <div className="animate-in fade-in zoom-in-95 relative w-full max-w-6xl duration-200">
            <button
              className="absolute top-2 right-2 z-10 cursor-pointer rounded-full bg-white/20 px-3 py-1 text-white transition-colors hover:bg-white/30"
              onClick={() => setActive(null)}
              aria-label="Close video"
            >
              ✕
            </button>
            <PlyrPlayer
              src={convertFileSrc(active.path)}
              title={active.metadata?.name || ''}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Videos;
