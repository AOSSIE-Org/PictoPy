'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

interface Feature {
  title: string;
  description: string;
  icon: string;
}

const features: Feature[] = [
  {
    title: 'Smart Tagging',
    description:
      'Automatically tag photos based on detected objects and faces.',
    icon: '🏷️',
  },
  {
    title: 'Album Management',
    description: 'Easily organize your photos into albums with AI suggestions.',
    icon: '📁',
  },
  {
    title: 'Advanced Image Analysis',
    description: 'Analyze image content for smarter organization and search.',
    icon: '🧠',
  },
  {
    title: 'Privacy & Offline Access',
    description: 'Your data stays with you. Full offline access and privacy.',
    icon: '🔒',
  },
];

export const AppFeatures: React.FC = () => {
  const [featureIndex, setFeatureIndex] = useState(0);
  const currentFeature = features[featureIndex];

  useEffect(() => {
    const interval = setInterval(() => {
      setFeatureIndex((prev) => (prev + 1) % features.length);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="flex max-h-full w-1/2 flex-col justify-center border p-4">
      <CardHeader className="p-6 pb-4">
        <h2 className="text-center text-xl font-semibold" />
      </CardHeader>

      <CardContent className="flex flex-1 flex-col items-center justify-center space-y-3 p-6 text-center">
        <div className="text-5xl">{currentFeature.icon}</div>
        <h2 className="text-lg font-semibold">{currentFeature.title}</h2>
        <p className="text-muted-foreground text-sm">
          {currentFeature.description}
        </p>

        <div className="flex justify-center gap-1 pt-2">
          {features.map((_, index) => (
            <div
              key={index}
              className={`h-2 w-2 rounded-full ${
                index === featureIndex
                  ? 'bg-foreground'
                  : 'bg-muted-foreground/40'
              }`}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
