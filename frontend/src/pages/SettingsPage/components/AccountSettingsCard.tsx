import React, { useState } from 'react'; // No need for useEffect
import { useDispatch } from 'react-redux';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { setAvatar, setName } from '@/features/onboardingSlice';
import { User } from 'lucide-react';
import SettingsCard from './SettingsCard';
import { avatars } from '@/constants/avatars';
import { CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const AccountSettingsCard: React.FC = () => {
  const dispatch = useDispatch();
  const [name, setLocalName] = useState(
    () => localStorage.getItem('name') || '',
  );
  const [selectedAvatar, setLocalAvatar] = useState(() => {
    const stored = localStorage.getItem('avatar') || '';
    return avatars.includes(stored) ? stored : '';
  });
  const [nameError, setNameError] = useState(false);

  // The redundant useEffect has been removed.

  const handleAvatarSelect = (avatar: string) => {
    setLocalAvatar(avatar);
  };

  const handleNameChange = (value: string) => {
    setLocalName(value);
    if (nameError) {
      setNameError(false);
    }
  };

  const handleSave = () => {
    if (!name.trim()) {
      setNameError(true);
      return;
    }

    setNameError(false);
    if (!selectedAvatar) return;

    try {
      dispatch(setName(name));
      dispatch(setAvatar(selectedAvatar));
      localStorage.setItem('name', name);
      localStorage.setItem('avatar', selectedAvatar);
    } catch (error) {
      console.error('Failed to save settings:');
    }
  };

  return (
    <SettingsCard
      icon={User}
      title="Account Information"
      description="Manage your account details and profile information."
    >
      <CardContent className="flex-1 space-y-6 overflow-y-hidden p-1 px-2">
        <div className="w-fit space-y-6">
          {/* Name Change */}
          <div className="w-full">
            <Label htmlFor="name" className="mb-2 block text-base font-medium">
              Name
            </Label>
            <Input
              id="name"
              placeholder={
                nameError ? "Name can't be empty" : 'Enter your name'
              }
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className={`h-10 w-full text-sm placeholder:text-sm ${
                nameError
                  ? 'border-red-500 placeholder:text-red-500/80 focus-visible:ring-red-500'
                  : ''
              }`}
            />
          </div>

          {/* Avatar Section */}
          <div className="w-full">
            <Label className="mb-3 block text-base font-medium">Avatar</Label>
            <div className="grid grid-cols-4 gap-8">
              {avatars.map((avatar) => {
                const isSelected = selectedAvatar === avatar;
                return (
                  <button
                    type="button"
                    key={avatar}
                    onClick={() => handleAvatarSelect(avatar)}
                    className={`bg-background relative inline-flex h-24 w-24 items-center justify-center rounded-full transition-all duration-300 ${
                      isSelected
                        ? 'ring-offset-background scale-90 ring-2 ring-blue-500 ring-offset-4'
                        : 'hover:ring-4 hover:ring-blue-500 hover:ring-offset-4'
                    }`}
                  >
                    <img
                      src={avatar}
                      alt="Avatar"
                      className={`h-24 w-24 rounded-full object-cover transition-all duration-300 ${
                        isSelected ? 'brightness-110' : ''
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Save Changes Button */}
        <Button
          className="mt-4 w-auto bg-blue-500 px-6 py-2 text-sm font-medium text-white hover:bg-blue-600"
          onClick={handleSave}
          disabled={!selectedAvatar}
        >
          Save Changes
        </Button>
      </CardContent>
    </SettingsCard>
  );
};

export default AccountSettingsCard;
