import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router';
import { selectAvatar, selectName } from '@/features/onboardingSelectors';
import { resetOnboarding } from '@/features/onboardingSlice';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { LogOut, User, Settings } from 'lucide-react';
import { Link } from 'react-router';
import { ROUTES } from '@/constants/routes';

/**
 * Profile page component
 * Displays user information and provides logout functionality
 */
const ProfilePage: React.FC = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const userName = useSelector(selectName);
    const userAvatar = useSelector(selectAvatar);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    const handleLogout = () => {
        setIsLoggingOut(true);
        dispatch(resetOnboarding());
        navigate('/');
    };

    const getAvatarSrc = () => {
        if (!userAvatar) return '/photo1.png';
        if (userAvatar.startsWith('data:')) return userAvatar;
        return convertFileSrc(userAvatar);
    };

    return (
        <div className="mx-auto flex-1 px-8 py-6">
            <div className="mx-auto max-w-2xl space-y-8">
                {/* Profile Card */}
                <Card className="overflow-hidden">
                    <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 pb-8 pt-8">
                        <div className="flex flex-col items-center space-y-4">
                            <div className="relative">
                                <img
                                    src={getAvatarSrc()}
                                    alt="User avatar"
                                    className="h-24 w-24 rounded-full border-4 border-background object-cover shadow-lg"
                                />
                                <div className="absolute -bottom-1 -right-1 rounded-full bg-primary p-2">
                                    <User className="h-4 w-4 text-primary-foreground" />
                                </div>
                            </div>
                            <div className="text-center">
                                <CardTitle className="text-2xl">
                                    {userName || 'User'}
                                </CardTitle>
                                <CardDescription className="mt-1">
                                    Welcome to your profile
                                </CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="space-y-4">
                            {/* User Info Section */}
                            <div className="rounded-lg bg-muted/50 p-4">
                                <h3 className="mb-3 text-sm font-medium text-muted-foreground">
                                    Account Information
                                </h3>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Name</span>
                                        <span className="font-medium">{userName || 'Not set'}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Quick Actions */}
                            <div className="flex flex-col gap-3 pt-4">
                                <Link to={`/${ROUTES.SETTINGS}`}>
                                    <Button variant="outline" className="w-full justify-start">
                                        <Settings className="mr-2 h-4 w-4" />
                                        Go to Settings
                                    </Button>
                                </Link>

                                {/* Logout Button with Confirmation */}
                                <AlertDialog>
                                    <AlertDialogTrigger asChild>
                                        <Button
                                            variant="destructive"
                                            className="w-full justify-start"
                                            disabled={isLoggingOut}
                                        >
                                            <LogOut className="mr-2 h-4 w-4" />
                                            {isLoggingOut ? 'Logging out...' : 'Logout'}
                                        </Button>
                                    </AlertDialogTrigger>
                                    <AlertDialogContent>
                                        <AlertDialogHeader>
                                            <AlertDialogTitle>
                                                Are you sure you want to logout?
                                            </AlertDialogTitle>
                                            <AlertDialogDescription>
                                                This will clear your profile data and return you to the
                                                initial setup screen. You will need to set up your
                                                profile again.
                                            </AlertDialogDescription>
                                        </AlertDialogHeader>
                                        <AlertDialogFooter>
                                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                                            <AlertDialogAction onClick={handleLogout}>
                                                Logout
                                            </AlertDialogAction>
                                        </AlertDialogFooter>
                                    </AlertDialogContent>
                                </AlertDialog>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default ProfilePage;
