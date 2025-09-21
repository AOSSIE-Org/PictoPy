import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SettingsCardProps {
  /**
   * Icon to display in the card header
   */
  icon: LucideIcon;
  /**
   * Card title
   */
  title: string;
  /**
   * Card description
   */
  description?: string;
  /**
   * Card content
   */
  children: React.ReactNode;
}

/**
 * Reusable settings card component with consistent styling
 */
const SettingsCard: React.FC<SettingsCardProps> = ({
  icon: Icon,
  title,
  description,
  children,
}) => {
  return (
    <div className="bg-card rounded-xl border p-6 shadow-sm">
      <div className="border-border mb-6 flex items-center gap-3 border-b pb-4">
        <Icon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        <div>
          <h2 className="text-card-foreground text-lg font-medium">{title}</h2>
          {description && (
            <p className="text-muted-foreground text-sm">{description}</p>
          )}
        </div>
      </div>
      {children}
    </div>
  );
};

export default SettingsCard;
