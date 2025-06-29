import { Loader } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { GlobalLoaderProps } from '@/types/loading.ts';

export const GlobalLoader: React.FC<GlobalLoaderProps> = ({
  loading,
  message,
}) => {
  return loading ? (
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
