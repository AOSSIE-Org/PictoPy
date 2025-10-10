import { useEffect, useState } from 'react';
import { Input } from '@/components/ui/input';
import { ThemeSelector } from '@/components/ThemeToggle';
import { Bell, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDispatch, useSelector } from 'react-redux';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { clearSearch } from '@/features/searchSlice';
import { convertFileSrc } from '@tauri-apps/api/core';
import { FaceSearchDialog } from '@/components/Dialog/FaceSearchDialog';
import { RootState } from '@/app/store';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters } from '@/api/api-functions';
import { setClusters } from '@/features/faceClustersSlice';
import { useNavigate } from 'react-router';
import { Cluster } from '@/types/Media';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export function Navbar() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);
  const searchState = useSelector((state: any) => state.search);
  const isSearchActive = searchState.active;
  const queryImage = searchState.queryImage;

  const [isFocused, setIsFocused] = useState(false);

  const { clusters } = useSelector((state: RootState) => state.faceClusters);
  const { data: clustersData, isSuccess: clustersSuccess } = usePictoQuery({
    queryKey: ['clusters'],
    queryFn: fetchAllClusters,
  });

  useEffect(() => {
    if (clustersSuccess && clustersData?.data?.clusters) {
      const clusters = (clustersData.data.clusters || []) as Cluster[];
      dispatch(setClusters(clusters));
    }
  }, [clustersData, clustersSuccess, dispatch]);

  const handlePersonClick = (clusterId: string) => {
    navigate(`/person/${clusterId}`);
    setIsFocused(false);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsFocused(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <div className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b pr-4 backdrop-blur">
        {/* Logo */}
        <div className="flex w-[256px] items-center justify-center">
          <a href="/" className="flex items-center space-x-2">
            <img src="/128x128.png" width={32} height={32} alt="PictoPy Logo" />
            <span className="text-xl font-bold">PictoPy</span>
          </a>
        </div>

        {/*  Search Bar */}
        <div className="mx-auto flex max-w-md flex-1 justify-center px-4">
          <div
            className={`dark:bg-muted/50 flex w-full items-center gap-1 rounded-md bg-neutral-100 px-1 py-1 transition-transform duration-200 ${
              isFocused ? 'scale-110 ring-2 ring-neutral-400' : ''
            }`}
          >
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
                    className="absolute -top-1 -right-1 flex h-3 w-3 cursor-pointer items-center justify-center rounded-full bg-red-600 text-[10px] leading-none text-white"
                  >
                    ✕
                  </button>
                )}
              </div>
            )}

            {/* Input */}
            <Input
              type="search"
              placeholder="Search photos, people, or places..."
              className="mr-2 flex-1 border-0 bg-neutral-200 focus-visible:ring-0"
              onFocus={() => setIsFocused(true)}
            />

            {/* FaceSearch Dialog */}
            <FaceSearchDialog />

            <button className="text-muted-foreground hover:bg-accent dark:hover:bg-accent/50 hover:text-foreground mx-1 rounded-sm p-2">
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
      {/* info about the search bar  */}
      {isFocused && (
        <>
          {/* Background Blur */}
          <div
            className="animate-in fade-in fixed inset-0 z-30 bg-black/40 backdrop-blur-sm duration-200"
            onClick={() => setIsFocused(false)}
          />

          {/* Floating Search Panel */}
          <div
            className="animate-in fade-in slide-in-from-top-5 fixed top-16 left-1/2 z-40 max-h-[60vh] w-[90vw] max-w-[700px] -translate-x-1/2 overflow-y-auto rounded-xl bg-white p-6 shadow-2xl transition-all duration-300 dark:bg-neutral-900"
            onClick={(e) => e.stopPropagation()} // prevents accidental close
          >
            {/* Header */}
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-neutral-700 dark:text-neutral-200">
                Recent Searches
              </h3>
              <button
                className="text-sm text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
                onClick={() => console.log('Clear history')}
              >
                Clear
              </button>
            </div>

            {/* Recent Searches Chips */}
            <div className="mb-6 flex flex-wrap gap-3">
              {['Beach trip', 'Riya', 'Office', 'Birthday', 'Graduation'].map(
                (item) => (
                  <span
                    key={item}
                    className="cursor-pointer rounded-full bg-neutral-200 px-4 py-2 text-sm text-neutral-800 hover:bg-neutral-300 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
                  >
                    {item}
                  </span>
                ),
              )}
            </div>

            {/* Faces Section */}
            <h3 className="mb-3 text-lg font-semibold text-neutral-700 dark:text-neutral-200">
              Faces
            </h3>
            {clusters.length === 0 ? (
              <>
                <p className="mb-4 text-sm text-neutral-500 dark:text-neutral-400">
                  No faces found. PictoPy will automatically detect and group
                  faces as you add more photos.
                </p>
              </>
            ) : (
              <>
                <div className="grid grid-cols-5 gap-4">
                  {clusters.map((cluster: any) => (
                    <div
                      key={cluster.cluster_id}
                      className="hover:bg-accent flex cursor-pointer flex-col items-center gap-2 rounded-lg p-4 transition-colors dark:hover:bg-white/10"
                      onClick={() => handlePersonClick(cluster.cluster_id)}
                    >
                      <Avatar className="border-accent-foreground w-16 border-[1px] md:h-20 md:w-20">
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
                      <div className="text-center">
                        <p className="font-medium">
                          {cluster.cluster_name ||
                            `Person ${cluster.cluster_id.slice(-4)}`}
                        </p>
                        <p className="text-muted-foreground text-xs">
                          {cluster.face_count} photo
                          {cluster.face_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </>
      )}
    </>
  );
}
