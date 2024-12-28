import React from 'react';
import { Progress } from "@/components/ui/progress"
export const LoadingScreen: React.FC = () => <div>
    <Progress value={33} />
</div>;
