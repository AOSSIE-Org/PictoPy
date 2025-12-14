import { useDispatch, useSelector } from 'react-redux';
import { useState } from 'react';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { resetOnboarding } from '@/features/onboardingSlice';
import { LogoutDialog } from '@/components/Dialog/LogoutDialog';
import { useTheme } from '@/contexts/ThemeContext';

const ProfilePage = () => {
  const dispatch = useDispatch();
  const { theme } = useTheme();

  const userName = useSelector(selectName);
  const userAvatar = useSelector(selectAvatar);

  const [showLogout, setShowLogout] = useState(false);

  const completion = (userAvatar ? 50 : 0) + (userName ? 50 : 0);

  const handleLogout = () => {
    dispatch(resetOnboarding());
    window.location.href = '/';
  };

  return (
    <div className="bg-background text-foreground flex h-full justify-center overflow-y-auto px-4 py-8">
      <div className="w-full max-w-3xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-muted-foreground text-xs font-semibold tracking-[0.2em] uppercase">
              Your Account
            </p>
            <h1 className="text-2xl font-bold">Profile</h1>
          </div>

          <span className="border-border bg-muted text-muted-foreground rounded-full border px-3 py-1 text-xs">
            Logged in
          </span>
        </div>

        {/* Card */}
        <div className="border-border bg-background rounded-2xl border p-6 shadow-lg sm:p-8">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
            {/* Avatar */}
            <div className="relative">
              <div className="border-border bg-muted h-24 w-24 rounded-full border-4 shadow-xl ring-2 ring-indigo-500/50">
                <img
                  src={userAvatar || '/photo1.png'}
                  alt="User avatar"
                  className="h-full w-full rounded-full object-cover"
                />
              </div>
            </div>

            {/* Info */}
            <div className="flex-1">
              <h2 className="text-xl font-semibold">
                {userName || 'Guest User'}
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Manage your personal info, security, and preferences.
              </p>

              {/* Meta */}
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="border-border bg-muted rounded-full border px-3 py-1">
                  Profile completion: {completion}%
                </span>

                <span className="border-border bg-muted rounded-full border px-3 py-1">
                  Theme: {theme}
                </span>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="border-border my-6 border-t" />

          {/* Actions */}
          <div className="grid gap-3 sm:grid-cols-3">
            <a
              href="/profile/edit"
              className="border-border bg-muted hover:bg-accent flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-medium"
            >
              <span>Edit Profile</span>
              <span className="text-muted-foreground text-xs">⌘E</span>
            </a>

            <a
              href="/settings"
              className="border-border bg-muted hover:bg-accent flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-medium"
            >
              <span>Account Settings</span>
              <span className="text-muted-foreground text-xs">⚙</span>
            </a>

            <button
              onClick={() => setShowLogout(true)}
              className="border-destructive/40 bg-destructive/5 text-destructive hover:bg-destructive/15 flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-medium"
            >
              <span>Logout</span>
              <span className="text-xs">⟶</span>
            </button>
          </div>
        </div>
      </div>

      {/* Logout Dialog */}
      <LogoutDialog
        open={showLogout}
        onCancel={() => setShowLogout(false)}
        onConfirm={handleLogout}
      />
    </div>
  );
};

export default ProfilePage;
