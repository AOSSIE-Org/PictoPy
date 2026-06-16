import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { startTextSearch, clearSearch } from '@/features/searchSlice';

import { Input } from '@/components/ui/input';
import { ThemeSelector } from '@/components/ThemeToggle';
import { Search, Heart, ArrowRight } from 'lucide-react';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { convertFileSrc } from '@tauri-apps/api/core';
import { FaceSearchDialog } from '@/components/Dialog/FaceSearchDialog';
import { Link, useNavigate } from 'react-router';
import { useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ROUTES } from '@/constants/routes';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { RootState } from '@/app/store';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters } from '@/api/api-functions';
import { setClusters } from '@/features/faceClustersSlice';
import { Cluster } from '@/types/Media';

export function Navbar() {
  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);
  const queryImage = useSelector((state: any) => state.search.queryImage);
  const dispatch = useDispatch();
  const [searchInput] = useState('');
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

  const navigate = useNavigate();

  const [isExpanded, setIsExpanded] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setIsExpanded(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsExpanded(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const { clusters } = useSelector((state: RootState) => state.faceClusters);

  const { data: clustersData, isSuccess: clustersSuccess } = usePictoQuery({
    queryKey: ['clusters'],
    queryFn: fetchAllClusters,
    enabled: isExpanded && (!clusters || clusters.length === 0),
  });

  useEffect(() => {
    if (clustersSuccess && clustersData?.data?.clusters) {
      const fetchedClusters = (clustersData.data.clusters || []) as Cluster[];
      dispatch(setClusters(fetchedClusters));
    }
  }, [clustersData, clustersSuccess, dispatch]);

  const handleNavigate = (path: string) => {
    navigate(path);
    setIsExpanded(false);
  };

  return (
    <div className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b pr-4 backdrop-blur">
      {/* Logo */}
      <div className="flex w-[256px] items-center justify-center">
        <Link to="/" className="flex items-center space-x-2">
          <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
          <span className="text-xl font-bold">PictoPy</span>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="mx-auto flex max-w-lg flex-1 justify-center px-4">
        <div
          ref={wrapperRef}
          className="dark:bg-muted/50 relative flex w-full items-center gap-1 rounded-md bg-neutral-100 px-1 py-1"
        >
          {/* Query Image */}
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
            onFocus={() => setIsExpanded(true)}
            onClick={() => setIsExpanded(true)}
          />

          {/* FaceSearch Dialog */}
          <FaceSearchDialog />

          {/* Search Icon */}
          <button
            onClick={() => inputRef.current?.focus()}
            className="text-muted-foreground hover:bg-accent dark:hover:bg-accent/50 hover:text-foreground mx-1 rounded-sm p-2"
            title="Focus search"
          >
            <Search className="h-4 w-4" />
          </button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ type: 'tween', duration: 0.15 }}
                className="border-border bg-popover absolute top-full right-0 left-0 z-50 mt-1 overflow-hidden rounded-lg border shadow-lg"
              >
                <Separator />

                {/* FavoritesRow */}
                <button
                  type="button"
                  className="hover:bg-accent flex w-full cursor-pointer items-center justify-between px-4 py-3 transition-colors"
                  onClick={() => handleNavigate(`/${ROUTES.FAVOURITES}`)}
                >
                  <div className="flex items-center gap-2">
                    <Heart className="h-4 w-4" />
                    <span className="text-sm font-medium">Favourites</span>
                  </div>
                </button>

                <Separator />

                {/* FaceClustersRow */}
                {clusters && clusters.length > 0 && (
                  <div className="flex flex-row flex-nowrap justify-between overflow-hidden px-4">
                    {clusters.slice(0, 6).map((cluster: Cluster) => (
                      <button
                        type="button"
                        key={cluster.cluster_id}
                        className="hover:bg-accent flex cursor-pointer flex-col items-center gap-1 px-1 py-2 transition-opacity"
                        onClick={() =>
                          handleNavigate(`/person/${cluster.cluster_id}`)
                        }
                      >
                        <Avatar className="border-border h-10 w-10 border">
                          <AvatarImage
                            src={
                              cluster.face_image_base64
                                ? `data:image/jpeg;base64,${cluster.face_image_base64}`
                                : undefined
                            }
                            alt={cluster.cluster_name || 'Person'}
                          />
                          <AvatarFallback>
                            {cluster.cluster_name?.charAt(0).toUpperCase() ||
                              cluster.cluster_id.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <span className="block max-w-[56px] truncate text-center text-xs">
                          {cluster.cluster_name ||
                            `Person ${cluster.cluster_id.slice(-4)}`}
                        </span>
                      </button>
                    ))}
                  </div>
                )}

                <Separator />

                {/* SeeAllPeopleButton */}
                <button
                  type="button"
                  className="text-muted-foreground hover:text-foreground hover:bg-accent flex w-full cursor-pointer items-center justify-center gap-1 px-4 py-2 text-sm transition-colors"
                  onClick={() => handleNavigate(`/${ROUTES.AI}`)}
                >
                  <ArrowRight className="h-4 w-4" />
                  <span>See all people</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Right Side */}
      <div className="flex items-center space-x-4">
        <ThemeSelector />
        <div className="flex items-center space-x-2">
          <span className="hidden text-sm sm:inline-block">
            Welcome{' '}
            <span
              className="text-muted-foreground inline-block max-w-[150px] truncate align-bottom"
              title={userName}
            >
              {userName?.split(' ')[0] ?? ''}
            </span>
          </span>
          <Link to="/settings#account" className="p-2">
            <img
              src={userAvatar || '/photo1.png'}
              className="hover:ring-primary/50 h-8 w-8 cursor-pointer rounded-full transition-all hover:ring-2"
              alt="User avatar"
            />
          </Link>
        </div>
      </div>
    </div>
  );
}
