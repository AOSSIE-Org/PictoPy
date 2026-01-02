import { useEffect, useState, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
    MoreVertical,
    Search,
    Merge,
    Eye,
    EyeOff,
} from 'lucide-react';
import { RootState } from '@/app/store';
import {
    setClusters,
    setMergingMode,
    toggleSelectClusterForMerge,
    toggleIgnoreClusterLocal,
} from '@/features/faceClustersSlice';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import {
    fetchAllClusters,
    mergeClusters,
    toggleIgnoreCluster,
} from '@/api/api-functions/face_clusters';
import { Cluster } from '@/types/Media';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export function PeoplePage() {
    const navigate = useNavigate();
    const dispatch = useDispatch();
    const [searchQuery, setSearchQuery] = useState('');
    const [showIgnored, setShowIgnored] = useState(false);

    const { clusters, isMergingMode, selectedClusterIdsForMerge } = useSelector(
        (state: RootState) => state.faceClusters,
    );

    const {
        data: clustersData,
        isSuccess: clustersSuccess,
        refetch,
    } = usePictoQuery({
        queryKey: ['clusters'],
        queryFn: fetchAllClusters,
    });

    const mergeMutation = usePictoMutation({
        mutationFn: mergeClusters,
        onSuccess: () => {
            dispatch(setMergingMode(false));
            refetch();
        },
    });

    useMutationFeedback(mergeMutation, {
        loadingMessage: 'Merging clusters...',
        successMessage: 'Clusters merged successfully!',
        errorMessage: 'Failed to merge clusters.',
    });

    const ignoreMutation = usePictoMutation({
        mutationFn: toggleIgnoreCluster,
        onSuccess: (_data, variables) => {
            dispatch(
                toggleIgnoreClusterLocal({
                    clusterId: variables.cluster_id,
                    isIgnored: variables.is_ignored,
                }),
            );
        },
    });

    useEffect(() => {
        if (clustersSuccess && clustersData?.data?.clusters) {
            const clusters = (clustersData.data.clusters || []) as Cluster[];
            dispatch(setClusters(clusters));
        }
    }, [clustersData, clustersSuccess, dispatch]);

    const filteredClusters = useMemo(() => {
        return clusters.filter((cluster) => {
            const matchesSearch =
                (cluster.cluster_name || `Person ${cluster.cluster_id.slice(-4)}`)
                    .toLowerCase()
                    .includes(searchQuery.toLowerCase());
            const matchesIgnore = showIgnored ? cluster.is_ignored : !cluster.is_ignored;
            return matchesSearch && matchesIgnore;
        });
    }, [clusters, searchQuery, showIgnored]);

    const handlePersonClick = (cluster_id: string) => {
        if (isMergingMode) {
            dispatch(toggleSelectClusterForMerge(cluster_id));
        } else {
            navigate(`/person/${cluster_id}`);
        }
    };

    const handleMerge = () => {
        if (selectedClusterIdsForMerge.length === 2) {
            mergeMutation.mutate({
                source_cluster_id: selectedClusterIdsForMerge[0],
                target_cluster_id: selectedClusterIdsForMerge[1],
            });
        }
    };

    const handleToggleIgnore = (cluster_id: string, currentlyIgnored: boolean) => {
        ignoreMutation.mutate({
            cluster_id,
            is_ignored: !currentlyIgnored,
        });
    };

    return (
        <div className="p-6">
            <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">People</h1>
                    <p className="text-muted-foreground">
                        Manage detected faces and group them into people.
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    {isMergingMode ? (
                        <>
                            <Button
                                variant="outline"
                                onClick={() => dispatch(setMergingMode(false))}
                            >
                                Cancel
                            </Button>
                            <Button
                                disabled={selectedClusterIdsForMerge.length !== 2}
                                onClick={handleMerge}
                            >
                                <Merge className="mr-2 h-4 w-4" />
                                Merge Selected ({selectedClusterIdsForMerge.length}/2)
                            </Button>
                        </>
                    ) : (
                        <Button variant="outline" onClick={() => dispatch(setMergingMode(true))}>
                            <Merge className="mr-2 h-4 w-4" />
                            Merge Mode
                        </Button>
                    )}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setShowIgnored(!showIgnored)}
                        title={showIgnored ? "Show Active" : "Show Ignored"}
                    >
                        {showIgnored ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    </Button>
                </div>
            </div>

            <div className="mb-6 flex items-center gap-4">
                <div className="relative flex-1">
                    <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
                    <Input
                        placeholder="Search people..."
                        className="pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
                {filteredClusters.map((cluster) => (
                    <div
                        key={cluster.cluster_id}
                        className={`group relative flex cursor-pointer flex-col items-center gap-3 rounded-xl p-4 transition-all hover:bg-accent/50 ${selectedClusterIdsForMerge.includes(cluster.cluster_id)
                            ? 'bg-primary/10 ring-2 ring-primary'
                            : ''
                            }`}
                        onClick={() => handlePersonClick(cluster.cluster_id)}
                    >
                        {isMergingMode && (
                            <div className="absolute top-2 left-2 z-10">
                                <Checkbox
                                    checked={selectedClusterIdsForMerge.includes(cluster.cluster_id)}
                                    onChange={() => dispatch(toggleSelectClusterForMerge(cluster.cluster_id))}
                                    onClick={(e: React.MouseEvent) => e.stopPropagation()}
                                />
                            </div>
                        )}

                        <div className="absolute top-2 right-2 z-10 opacity-0 transition-opacity group-hover:opacity-100">
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm">
                                        <MoreVertical className="h-4 w-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={(e: React.MouseEvent) => {
                                        e.stopPropagation();
                                        handleToggleIgnore(cluster.cluster_id, cluster.is_ignored);
                                    }}>
                                        {cluster.is_ignored ? (
                                            <><Eye className="mr-2 h-4 w-4" /> Restore</>
                                        ) : (
                                            <><EyeOff className="mr-2 h-4 w-4" /> Ignore</>
                                        )}
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>

                        <Avatar className="h-24 w-24 border-2 border-background shadow-sm transition-transform group-hover:scale-105 md:h-28 md:w-28">
                            <AvatarImage
                                src={
                                    cluster.face_image_base64
                                        ? `data:image/jpeg;base64,${cluster.face_image_base64}`
                                        : undefined
                                }
                                alt={cluster.cluster_name || 'Person'}
                            />
                            <AvatarFallback className="text-xl">
                                {cluster.cluster_name?.charAt(0).toUpperCase() ||
                                    cluster.cluster_id.slice(-4).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>

                        <div className="text-center">
                            <p className="max-w-[120px] truncate font-semibold">
                                {cluster.cluster_name || `Person ${cluster.cluster_id.slice(-4)}`}
                            </p>
                            <p className="text-muted-foreground text-xs">
                                {cluster.face_count} photo
                                {cluster.face_count !== 1 ? 's' : ''}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {filteredClusters.length === 0 && (
                <div className="flex h-64 flex-col items-center justify-center rounded-xl border-2 border-dashed">
                    <p className="text-muted-foreground">No people found matching your criteria.</p>
                </div>
            )}
        </div>
    );
}
