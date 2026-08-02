import { useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ImageCard } from '@/components/Media/ImageCard';
import { Image } from '@/types/Media';
import { setCurrentViewIndex } from '@/features/imageSlice';
import { MediaView } from './MediaView';
import { selectIsImageViewOpen } from '@/features/imageSelectors';

interface RankedGalleryProps {
  images: Image[];
  title?: string;
  titleRight?: React.ReactNode;
}

export function RankedGallery({
  images,
  title,
  titleRight,
}: RankedGalleryProps) {
  const dispatch = useDispatch();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);

  // Maps image ID → index in the flat input array for the viewer
  const imageIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    images.forEach((img, idx) => map.set(img.id, idx));
    return map;
  }, [images]);

  return (
    <>
      <div>
        {title && (
          <div className="mt-6 mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold">{title}</h1>
            {titleRight && <div>{titleRight}</div>}
          </div>
        )}
        <div className="grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4 p-2">
          {images.map((img) => (
            <div key={img.id} className="group relative">
              <ImageCard
                image={img}
                onClick={() =>
                  dispatch(setCurrentViewIndex(imageIndexMap.get(img.id) ?? -1))
                }
                className="w-full transition-transform duration-200 group-hover:scale-105"
              />
            </div>
          ))}
        </div>
      </div>
      {isImageViewOpen && <MediaView images={images} />}
    </>
  );
}
