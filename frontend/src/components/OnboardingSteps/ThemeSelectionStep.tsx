'use client';

import '@/App.css'; // this is important
import { useEffect, useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';

export function ThemeSelectionStep({
  onBack,
  onComplete,
}: {
  onBack: () => void;
  onComplete: () => void;
}) {
  const [theme, setTheme] = useState('system');

  useEffect(() => {
    const stored = localStorage.getItem('theme') || 'system';
    setTheme(stored);
  }, []);

  useEffect(() => {
    if (theme === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute(
        'data-theme',
        isDark ? 'dark' : 'light',
      );
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <div className="mb-10 flex min-h-screen w-full items-start justify-center overflow-auto p-4">
      <div className="border-border bg-card mt-16 mb-24 flex w-full max-w-5xl flex-col rounded-2xl border shadow-xl">
        <CardHeader className="border-border border-b p-6 pb-4">
          <div className="text-muted-foreground mb-1 flex justify-between text-xs">
            <span>Step 3 of 3</span>
            <span>100%</span>
          </div>
          <div className="bg-muted mb-4 h-2 w-full rounded-full">
            <div
              className="bg-primary h-full rounded-full transition-all duration-300"
              style={{ width: `100%` }}
            />
          </div>

          <CardTitle className="text-2xl font-semibold">
            Choose Your Theme
          </CardTitle>
          <p className="text-muted-foreground mt-2 text-base">
            Select your preferred appearance
          </p>
        </CardHeader>

        <CardContent className="flex-1 space-y-10 p-6 text-[17px]">
          <RadioGroup
            value={theme}
            onValueChange={setTheme}
            className="space-y-8"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="light" id="light" />
              <Label htmlFor="light">🌞 Light Mode</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="dark" id="dark" />
              <Label htmlFor="dark">🌙 Dark Mode</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="system" id="system" />
              <Label htmlFor="system">🖥️ System Default</Label>
            </div>
          </RadioGroup>
        </CardContent>

        <CardFooter className="border-border flex justify-between border-t p-6 pb-20">
          <Button
            variant="outline"
            onClick={onBack}
            className="mt-8 px-5 py-5 text-sm"
          >
            Back
          </Button>
          <Button onClick={onComplete} className="mt-8 px-5 py-5 text-sm">
            Complete ✔
          </Button>
        </CardFooter>
      </div>
    </div>
  );
}
