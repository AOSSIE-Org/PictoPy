import { useDispatch, useSelector } from 'react-redux';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { setAvatar, setName } from '@/features/onboardingSlice';
import { Input } from '@/components/ui/input';
import { useState } from 'react';

const EditProfilePage = () => {
  const dispatch = useDispatch();

  const currentName = useSelector(selectName);
  const currentAvatar = useSelector(selectAvatar);

  const [name, setLocalName] = useState(currentName || '');
  const [avatar, setLocalAvatar] = useState(currentAvatar || '/photo1.png');

  const handleSave = () => {
    dispatch(setName(name));
    dispatch(setAvatar(avatar));
    window.location.href = '/profile';
  };

  return (
    <div className="bg-background flex h-full justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="mb-6 flex items-center gap-4">
          <a
            href="/profile"
            className="text-muted-foreground hover:text-foreground text-sm"
          >
            ← Back
          </a>
          <h1 className="text-2xl font-bold">Edit Profile</h1>
        </div>

        <div className="border-border bg-background rounded-xl border p-6">
          {/* Avatar */}
          <div className="mb-6 flex items-center gap-6">
            <img
              src={avatar}
              className="h-24 w-24 rounded-full border object-cover"
            />

            <input
              type="file"
              accept="image/*"
              id="avatar-upload"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                setLocalAvatar(URL.createObjectURL(file));
              }}
            />

            <button
              onClick={() => document.getElementById('avatar-upload')?.click()}
              className="hover:bg-accent rounded-md border px-4 py-2 text-sm"
            >
              Change Avatar
            </button>
          </div>

          {/* Name */}
          <div className="mb-6">
            <label className="mb-1 block text-sm font-medium">
              Display Name
            </label>
            <Input
              value={name}
              onChange={(e) => setLocalName(e.target.value)}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <a href="/profile">
              <button className="rounded-md border px-4 py-2">Cancel</button>
            </a>

            <button
              onClick={handleSave}
              className="bg-primary rounded-md px-4 py-2 text-white"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditProfilePage;
