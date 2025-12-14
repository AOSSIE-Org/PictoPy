import { useNavigate, useLocation } from 'react-router';
import { ArrowLeft, Calendar, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';

const MemoryDetail = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const memory = location.state?.memory;

  const handleBack = () => {
    navigate('/memories');
  };

  const openInGallery = () => {
    navigate('/gallery', {
      state: {
        startDate: memory.date_range_start,
        endDate: memory.date_range_end,
        latitude: memory.latitude,
        longitude: memory.longitude,
      },
    });
  };

  if (!memory) {
    navigate('/memories');
    return null;
  }

  const formatDateRange = (start: string, end: string) => {
    const s = new Date(start);
    const e = new Date(end);

    if (s.toDateString() === e.toDateString()) {
      return s.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      });
    }

    return `${s.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })} – ${e.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })}`;
  };

  return (
    <div className="flex h-full flex-col px-8 py-6">
      <Button
        onClick={handleBack}
        variant="ghost"
        className="mb-4 flex items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Memories
      </Button>

      <h1 className="mb-2 text-2xl font-bold">{memory.title}</h1>

      <div className="mb-6 flex flex-wrap gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          {formatDateRange(
            memory.date_range_start,
            memory.date_range_end,
          )}
        </div>

        {memory.location_name && (
          <div className="flex items-center gap-1">
            <MapPin className="h-4 w-4" />
            {memory.location_name}
          </div>
        )}

        <span>{memory.image_count} photos</span>
      </div>

      <Button onClick={openInGallery}>
        View photos in Gallery
      </Button>
    </div>
  );
};

export default MemoryDetail;
