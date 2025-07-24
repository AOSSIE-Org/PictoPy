import '@/App.css';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface AvatarAndNameStepProps {
  onNext: () => void;
  stepIndex: number;
  totalSteps: number;
}

const avatars = [
  '/avatars/avatar1.png',
  '/avatars/avatar2.png',
  '/avatars/avatar3.png',
  '/avatars/avatar4.png',
  '/avatars/avatar5.png',
  '/avatars/avatar6.png',
  '/avatars/avatar7.png',
  '/avatars/avatar8.png',
];

export const AvatarAndNameStep: React.FC<AvatarAndNameStepProps> = ({
  onNext,
  stepIndex,
  totalSteps,
}) => {
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
  const [name, setName] = useState('');

  const handleAvatarSelect = (avatar: string) => {
    setSelectedAvatar(avatar);
  };

  const handleNextClick = () => {
    if (name && selectedAvatar) {
      onNext();
    } else {
      alert('Please enter your name and select an avatar.');
    }
  };

  return (
    <div className="bg-background text-foreground min-h-screen w-full overflow-y-auto px-4 py-12">
      <Card className="border-border mx-auto flex w-full max-w-4xl flex-col justify-between border p-8 shadow-sm">
        <div>
          {/* Progress Header */}
          <CardHeader>
            <div className="text-muted-foreground mb-1 flex justify-between text-sm">
              <span>
                Step {stepIndex} of {totalSteps}
              </span>
              <span>{Math.round((stepIndex / totalSteps) * 100)}%</span>
            </div>
            <div className="bg-muted mb-4 h-2 w-full rounded-full">
              <div
                className="bg-primary h-full rounded-full transition-all duration-300"
                style={{ width: `${(stepIndex / totalSteps) * 100}%` }}
              />
            </div>
          </CardHeader>

          {/* Step Title */}
          <h2 className="mb-2 text-2xl font-bold">Welcome to PictoPy</h2>
          <p className="text-muted-foreground mb-6">
            Let's get to know you a little better
          </p>

          {/* Name Input */}
          <div className="mb-6">
            <Label htmlFor="name" className="mb-2 block">
              Your Name
            </Label>
            <Input
              id="name"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="h-9 w-full text-base placeholder:text-base"
            />
          </div>

          {/* Avatar Selection */}
          <div className="mb-4">
            <Label className="mb-4 block">Choose Your Avatar</Label>
            <div className="grid grid-cols-4 gap-4">
              {avatars.map((avatar) => (
                <button
                  type="button"
                  key={avatar}
                  onClick={() => handleAvatarSelect(avatar)}
                  className={`rounded-full border-2 p-1 transition ${
                    selectedAvatar === avatar
                      ? 'border-primary'
                      : 'border-transparent'
                  }`}
                >
                  <img
                    src={avatar}
                    alt="Avatar"
                    className="h-20 w-20 rounded-full"
                  />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Next Button */}
        <div className="mt-10 flex justify-end">
          <Button className="px-7 py-3 text-base" onClick={handleNextClick}>
            Next
          </Button>
        </div>
      </Card>
    </div>
  );
};
