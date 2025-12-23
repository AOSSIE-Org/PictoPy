import { useEffect, useMemo, useState } from 'react';
import { useDispatch } from 'react-redux';

import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchMemories } from '@/api/api-functions/memories';
import { fetchAllImages } from '@/api/api-functions';

import { AppDispatch } from '@/app/store';
import { setImages } from '@/features/imageSlice';

import { Image } from '@/types/Media';
import { Memory } from '@/types/Memory';

import { ChronologicalGallery } from '@/components/Media/ChronologicalGallery';
import { ImageCard } from '@/components/Media/ImageCard';

export const Memories = () => {
  const dispatch = useDispatch<AppDispatch>();

  const [activeMemory, setActiveMemory] = useState<Memory | null>(null);
  const [allImages, setAllImages] = useState<Image[]>([]);

  /* -----------------------------
     Fetch memories
  ----------------------------- */
  const { data, isSuccess } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: fetchMemories,
  });

  const memories: Memory[] = useMemo(() => {
    if (!isSuccess || !data?.data) return [];
    return data.data as Memory[];
  }, [data, isSuccess]);

  /* -----------------------------
     Fetch all images ONCE
  ----------------------------- */
  useEffect(() => {
    fetchAllImages().then((res) => {
      setAllImages(res.data as Image[]);
    });
  }, []);

  /* -----------------------------
     Open memory
  ----------------------------- */
  useEffect(() => {
    if (!activeMemory) return;

    const filtered = allImages.filter((img) =>
      activeMemory.image_ids.includes(img.id),
    );

    dispatch(setImages(filtered));
  }, [activeMemory, allImages, dispatch]);

  /* -----------------------------
     MEMORY VIEW
  ----------------------------- */
  if (activeMemory) {
    return (
      <div className="relative h-full">
        <button
          onClick={() => setActiveMemory(null)}
          className="bg-background sticky top-0 z-20 mb-2 py-3 text-sm font-medium hover:text-indigo-500"
        >
          ← Back to Memories
        </button>

        <ChronologicalGallery
          images={allImages.filter((img) =>
            activeMemory.image_ids.includes(img.id),
          )}
          showTitle
          title={activeMemory.title}
        />
      </div>
    );
  }

  /* -----------------------------
     Thumbnail helper
  ----------------------------- */
  const getThumb = (m: Memory) =>
    allImages.find((i) => i.id === m.image_ids[0]);

  /* -----------------------------
     MEMORIES UI
  ----------------------------- */
  return (
    <div className="px-8 pt-6">
      <h1 className="mb-4 text-2xl font-bold">Memories</h1>

      {memories.length === 0 && (
        <p className="text-muted-foreground text-sm">
          No memories yet. Keep capturing moments!
        </p>
      )}

      <div className="flex gap-6 overflow-x-auto pb-6">
        {memories.map((m) => {
          const thumb = getThumb(m);

          return (
            <div
              key={m.id}
              onClick={() => setActiveMemory(m)}
              className="group relative h-62 w-[260px] cursor-pointer overflow-hidden rounded-xl"
            >
              {thumb ? (
                <ImageCard image={thumb} className="h-full w-full" />
              ) : (
                <div className="flex h-full items-center justify-center text-xs text-gray-400">
                  No image
                </div>
              )}

              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

              <div className="absolute right-4 bottom-4 left-4 text-white">
                <p className="text-xs tracking-wide uppercase opacity-80">
                  {m.subtitle}
                </p>
                <h3 className="text-lg font-semibold">{m.title}</h3>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
