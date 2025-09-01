import { Clock, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const ComingSoon = () => {
  return (
    <div className="flex h-full items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center space-y-4 p-6 text-center">
          {/* Icon */}
          <div className="relative">
            <div className="bg-primary/10 flex h-16 w-16 items-center justify-center rounded-full">
              <Clock className="text-primary h-8 w-8" />
            </div>
            <div className="absolute -top-1 -right-1">
              <Sparkles className="h-5 w-5 text-yellow-500" />
            </div>
          </div>

          {/* Badge */}
          <Badge variant="secondary" className="px-3 py-1">
            Coming Soon
          </Badge>

          {/* Title */}
          <h1 className="text-xl font-bold tracking-tight">
            Feature in Development
          </h1>

          {/* Message */}
          <p className="text-muted-foreground text-sm">
            We're working hard to bring you something amazing. This feature will
            be available in a future update.
          </p>

          {/* Additional Info */}
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-muted-foreground text-xs">
              Stay tuned for updates and new features that will enhance your
              PictoPy experience!
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
