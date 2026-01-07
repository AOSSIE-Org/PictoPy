import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Camera, Upload, Image as ImageIcon } from 'lucide-react';
import { avatars } from '@/constants/avatars';
import { avatarApi } from '@/api/avatar';

interface AvatarUpdateCardProps {
  currentAvatar?: string;
  onAvatarUpdate: (avatarUrl: string) => void;
}

export const AvatarUpdateCard: React.FC<AvatarUpdateCardProps> = ({
  currentAvatar,
  onAvatarUpdate,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
      alert('Please select a PNG or JPG image');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    setIsUploading(true);
    try {
      const result = await avatarApi.uploadAvatar(file);
      const avatarUrl = avatarApi.getAvatarUrl(result.avatar_url);
      onAvatarUpdate(avatarUrl);
    } catch (error) {
      console.error('Avatar upload failed:', error);
      alert(`Failed to upload avatar: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handlePresetSelect = (avatar: string) => {
    setSelectedPreset(avatar);
    onAvatarUpdate(avatar);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="h-5 w-5" />
          Profile Photo
        </CardTitle>
        <CardDescription>
          Choose your profile photo from our collection or upload your own
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Photo */}
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={currentAvatar} alt="Profile photo" />
            <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600">
              <ImageIcon className="h-6 w-6 text-white" />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <p className="font-medium">Your current photo</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="mt-2"
            >
              <Upload className="h-4 w-4 mr-2" />
              {isUploading ? 'Uploading...' : 'Upload Photo'}
            </Button>
            <p className="text-xs text-muted-foreground mt-1">PNG, JPG up to 5MB</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>

        {/* Photo Gallery */}
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">or choose from gallery</p>
          <div className="grid grid-cols-4 gap-2">
            {avatars.map((avatar, index) => (
              <button
                key={avatar}
                onClick={() => handlePresetSelect(avatar)}
                className={`rounded-lg overflow-hidden transition-all duration-200 ${
                  selectedPreset === avatar || currentAvatar === avatar
                    ? 'ring-2 ring-primary'
                    : 'hover:scale-105'
                }`}
              >
                <Avatar className="h-14 w-14">
                  <AvatarImage src={avatar} alt={`Photo ${index + 1}`} />
                  <AvatarFallback>
                    <ImageIcon className="h-5 w-5" />
                  </AvatarFallback>
                </Avatar>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};