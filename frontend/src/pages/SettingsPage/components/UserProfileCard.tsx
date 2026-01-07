import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { AvatarUpdateCard } from '@/components/AvatarUpdateCard';
import { User, Save, Camera } from 'lucide-react';
import { useDispatch } from 'react-redux';
import { setName, setAvatar } from '@/features/onboardingSlice';
import { avatarApi } from '@/api/avatar';

export const UserProfileCard: React.FC = () => {
  const dispatch = useDispatch();
  const [name, setLocalName] = useState(localStorage.getItem('name') || '');
  const [currentAvatar, setCurrentAvatar] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Load current user preferences including avatar
  useEffect(() => {
    const loadUserPreferences = async () => {
      setIsLoading(true);
      try {
        const data = await avatarApi.getUserPreferences();
        const avatar = data.user_preferences?.avatar;
        if (avatar) {
          const avatarUrl = avatarApi.getAvatarUrl(avatar);
          setCurrentAvatar(avatarUrl);
        } else {
          // Fallback to localStorage avatar (from onboarding)
          const localAvatar = localStorage.getItem('avatar');
          if (localAvatar) {
            setCurrentAvatar(localAvatar);
          }
        }
      } catch (error) {
        console.error('Failed to load user preferences:', error);
        // Fallback to localStorage
        const localAvatar = localStorage.getItem('avatar');
        if (localAvatar) {
          setCurrentAvatar(localAvatar);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUserPreferences();
  }, []);

  const handleNameSave = async () => {
    setIsSaving(true);
    try {
      // Update localStorage and Redux state
      localStorage.setItem('name', name);
      dispatch(setName(name));
    } catch (error) {
      console.error('Failed to save name:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarUpdate = async (avatarUrl: string) => {
    try {
      // Update backend preferences
      await avatarApi.updateUserPreferences({ avatar: avatarUrl });
      
      setCurrentAvatar(avatarUrl);
      // Update localStorage and Redux state
      localStorage.setItem('avatar', avatarUrl);
      dispatch(setAvatar(avatarUrl));
    } catch (error) {
      console.error('Failed to update avatar:', error);
      alert(`Failed to update avatar: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Basic Profile Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profile Information
          </CardTitle>
          <CardDescription>
            Manage your display name and profile photo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-6">
            <div className="relative">
              <Avatar className="h-16 w-16">
                <AvatarImage src={currentAvatar || undefined} alt="Profile photo" />
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600">
                  <User className="h-6 w-6 text-white" />
                </AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-1 -right-1 bg-primary rounded-full p-1">
                <Camera className="h-3 w-3 text-primary-foreground" />
              </div>
            </div>
            <div className="flex-1 space-y-3">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm font-medium">Display Name</Label>
                <div className="flex gap-2">
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setLocalName(e.target.value)}
                    placeholder="Enter your name"
                    className="flex-1"
                  />
                  <Button
                    onClick={handleNameSave}
                    disabled={isSaving || !name.trim()}
                    size="sm"
                    className="px-4"
                  >
                    <Save className="h-4 w-4 mr-1" />
                    {isSaving ? 'Saving...' : 'Save'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Avatar Update */}
      <AvatarUpdateCard
        currentAvatar={currentAvatar || undefined}
        onAvatarUpdate={handleAvatarUpdate}
      />
    </div>
  );
};