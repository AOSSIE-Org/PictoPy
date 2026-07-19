import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { getPersonName } from '@/utils/personUtils';
import type { Cluster } from '@/types/Media';

interface PersonAvatarProps {
  cluster: Cluster;
  className?: string;
}

export function PersonAvatar({ cluster, className }: PersonAvatarProps) {
  return (
    <Avatar className={className}>
      <AvatarImage
        src={
          cluster.face_image_base64
            ? `data:image/jpeg;base64,${cluster.face_image_base64}`
            : undefined
        }
        alt={getPersonName(cluster)}
      />
      <AvatarFallback>
        {(cluster.cluster_name || cluster.cluster_id).charAt(0).toUpperCase()}
      </AvatarFallback>
    </Avatar>
  );
}
