'use client';
import '@/App.css';

import { useState, useEffect } from 'react';
import { AvatarAndNameStep } from '../components/OnboardingSteps/AvatarAndNameStep';
import { FolderSetupStep } from '../components/OnboardingSteps/FolderSetupStep';
import { ThemeSelectionStep } from '../components/OnboardingSteps/ThemeSelectionStep';

const features = [
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

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [featureIndex, setFeatureIndex] = useState(0);
  const totalSteps = 3;

  useEffect(() => {
    const interval = setInterval(() => {
      setFeatureIndex((prev) => (prev + 1) % features.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <AvatarAndNameStep
            stepIndex={step}
            totalSteps={totalSteps}
            onNext={() => setStep(2)}
          />
        );
      case 2:
        return (
          <FolderSetupStep
            stepIndex={step}
            totalSteps={totalSteps}
            onNext={() => setStep(3)}
            onBack={() => setStep(1)}
          />
        );
      case 3:
        return <ThemeSelectionStep onBack={() => setStep(2)} />;
      default:
        return null;
    }
  };

  const currentFeature = features[featureIndex];

  return (
    <div className="bg-background text-foreground flex min-h-screen">
      {/* Left Half: Step Cards */}
      <div className="bg-background flex h-screen w-1/2 items-center justify-center p-10">
        <div className="flex h-full w-full flex-col justify-center">
          {renderStep()}
        </div>
      </div>

      {/* Right Half: Features Showcase */}
      <div className="bg-muted text-muted-foreground flex w-1/2 flex-col items-center justify-center p-10 text-center">
        <div className="mb-4 text-6xl">{currentFeature.icon}</div>
        <h2 className="mb-2 text-2xl font-bold">{currentFeature.title}</h2>
        <p className="mb-6 text-sm">{currentFeature.description}</p>
        <div className="flex justify-center gap-2">
          {features.map((_, index) => (
            <div
              key={index}
              className={`h-2.5 w-2.5 rounded-full ${
                index === featureIndex
                  ? 'bg-foreground'
                  : 'bg-muted-foreground/40'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
