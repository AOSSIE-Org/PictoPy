import { useEffect, useState, useRef } from 'react';
import { Loader } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { GlobalLoaderProps } from '@/types/loading.ts';
import { MIN_LOADER_DISPLAY_TIME } from '@/config/pagination';

export const GlobalLoader: React.FC<GlobalLoaderProps> = ({
  loading,
  message,
}) => {
  const [visible, setVisible] = useState(loading);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (loading) {
      setVisible(true);
      startTimeRef.current = Date.now();
    } else if (startTimeRef.current) {
      const elapsed = Date.now() - startTimeRef.current;
      
      if (elapsed < MIN_LOADER_DISPLAY_TIME) {
        timerRef.current = setTimeout(() => {
          setVisible(false);
          startTimeRef.current = null;
        }, MIN_LOADER_DISPLAY_TIME - elapsed);
      } else {
        setVisible(false);
        startTimeRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [loading]);

  return visible ? (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="animate-in fade-in-0 zoom-in-95 flex flex-row items-center gap-3 p-6 duration-300">
        <Loader className="text-primary h-6 w-6 animate-spin" />
        <span className="font-medium">{message}</span>
      </Card>
    </div>
  ) : (
    <div></div>
  );
};
