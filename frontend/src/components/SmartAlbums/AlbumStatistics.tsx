import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Image, Grid3x3, Users, Sparkles, ImageIcon } from 'lucide-react';
import type { AlbumStatistics as AlbumStatisticsType } from '@/api/api-functions/smart_albums'; // ✅ Renamed with alias

interface AlbumStatisticsProps {
  statistics: AlbumStatisticsType | null; // ✅ Use the alias
}

interface StatCardProps {
  icon: React.ReactNode;
  title: string;
  value: number;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon, title, value, color }) => (
  <Card className="h-full">
    <CardContent className="p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-gray-600">{title}</div>
        </div>
      </div>
    </CardContent>
  </Card>
);

export const AlbumStatistics: React.FC<AlbumStatisticsProps> = ({ statistics }) => {
  if (!statistics) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <StatCard
        icon={<Image className="w-5 h-5 text-blue-600" />}
        title="Total Albums"
        value={statistics.total_albums}
        color="bg-blue-100"
      />
      <StatCard
        icon={<Grid3x3 className="w-5 h-5 text-cyan-600" />}
        title="Object Albums"
        value={statistics.object_albums}
        color="bg-cyan-100"
      />
      <StatCard
        icon={<Users className="w-5 h-5 text-purple-600" />}
        title="Face Albums"
        value={statistics.face_albums}
        color="bg-purple-100"
      />
      <StatCard
        icon={<Sparkles className="w-5 h-5 text-green-600" />}
        title="Auto-Update"
        value={statistics.auto_update_enabled}
        color="bg-green-100"
      />
      <StatCard
        icon={<ImageIcon className="w-5 h-5 text-orange-600" />}
        title="Total Images"
        value={statistics.total_images_in_albums}
        color="bg-orange-100"
      />
    </div>
  );
};