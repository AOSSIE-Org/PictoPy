import React from 'react';

interface SettingSwitchRowProps {
  /**
   * Base id used to derive the label/description ids referenced by
   * aria-labelledby / aria-describedby
   */
  id: string;
  /**
   * Row title
   */
  label: string;
  /**
   * Row description
   */
  description: string;
  /**
   * Whether the switch is on
   */
  checked: boolean;
  /**
   * Whether the switch is disabled (loading / pending / unknown state)
   */
  disabled: boolean;
  /**
   * Called when the switch is toggled
   */
  onToggle: () => void;
}

/**
 * Reusable labeled toggle switch row used by the System settings card
 */
const SettingSwitchRow: React.FC<SettingSwitchRowProps> = ({
  id,
  label,
  description,
  checked,
  disabled,
  onToggle,
}) => {
  const labelId = `${id}-label`;
  const descId = `${id}-desc`;

  return (
    <div className="flex items-center justify-between py-1">
      <div>
        <div id={labelId} className="font-medium">
          {label}
        </div>
        <div id={descId} className="text-muted-foreground text-sm">
          {description}
        </div>
      </div>

      <button
        role="switch"
        aria-checked={checked}
        aria-labelledby={labelId}
        aria-describedby={descId}
        disabled={disabled}
        onClick={onToggle}
        className={[
          'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full',
          'transition-colors duration-200 ease-in-out',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          checked
            ? 'bg-primary focus-visible:ring-primary'
            : 'bg-gray-200 focus-visible:ring-gray-500 dark:bg-gray-700',
        ].join(' ')}
      >
        <span
          className={[
            'inline-block h-4 w-4 rounded-full bg-white shadow-md',
            'transition-transform duration-200 ease-in-out',
            checked ? 'translate-x-6' : 'translate-x-1',
          ].join(' ')}
        />
      </button>
    </div>
  );
};

export default SettingSwitchRow;
