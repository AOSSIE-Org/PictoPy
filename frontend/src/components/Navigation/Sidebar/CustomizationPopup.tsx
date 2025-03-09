import React from 'react';
import { X } from 'lucide-react';
import { CustomStyles, presetThemes } from './styles';

// Define the props interface for the CustomizationPopup component
interface CustomizationPopupProps {
  styles: CustomStyles; // Current styles
  setStyles: React.Dispatch<React.SetStateAction<CustomStyles>>; // Function to update styles
  onClose: () => void; // Function to close the popup
}

const CustomizationPopup: React.FC<CustomizationPopupProps> = ({
  styles,
  setStyles,
  onClose,
}) => {
  /**
   * Updates a specific style property in the `styles` state.
   * @param key - The key of the style property to update.
   * @param value - The new value for the style property.
   */
  const updateStyle = (key: keyof CustomStyles, value: string | number) => {
    setStyles((prev) => ({ ...prev, [key]: value }));
  };

  /**
   * Handles file upload for background images or videos.
   * @param event - The file input change event.
   * @param type - The type of file being uploaded ('image' or 'video').
   */
  const handleFileUpload = (
    event: React.ChangeEvent<HTMLInputElement>,
    type: 'image' | 'video',
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      if (type === 'image') {
        updateStyle('backgroundImage', `url(${url})`);
        updateStyle('backgroundVideo', ''); // Clear video if an image is set
      } else {
        updateStyle('backgroundVideo', url);
        updateStyle('backgroundImage', ''); // Clear image if a video is set
      }
    }
  };

  /**
   * Renders a control input for customizing a specific style property.
   * @param label - The label for the control.
   * @param key - The key of the style property being controlled.
   * @param type - The type of input control ('color', 'range', 'select', or 'file').
   * @param options - Additional options for the input control (e.g., min, max, choices, accept).
   */
  const renderControl = (
    label: string,
    key: keyof CustomStyles,
    type: 'color' | 'range' | 'select' | 'file',
    options?: {
      min?: number;
      max?: number;
      step?: number;
      choices?: string[];
      accept?: string;
    },
  ) => (
    <div className="mb-4">
      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      {type === 'color' && (
        <input
          type="color"
          value={styles[key] as string}
          onChange={(e) => updateStyle(key, e.target.value)}
          className="rounded h-8 w-full"
        />
      )}
      {type === 'range' && (
        <div className="flex items-center">
          <input
            type="range"
            min={options?.min}
            max={options?.max}
            step={options?.step}
            value={styles[key] as number}
            onChange={(e) => updateStyle(key, Number(e.target.value))}
            className="mr-2 w-full"
          />
          <span className="text-sm">{styles[key]}</span>
        </div>
      )}
      {type === 'select' && (
        <select
          value={styles[key] as string}
          onChange={(e) => updateStyle(key, e.target.value)}
          className="rounded w-full border bg-white p-2 text-gray-900 dark:bg-gray-700 dark:text-gray-100"
        >
          {options?.choices?.map((choice) => (
            <option key={choice} value={choice}>
              {choice}
            </option>
          ))}
        </select>
      )}
      {type === 'file' && (
        <>
          <input
            type="file"
            accept={options?.accept}
            onChange={(e) =>
              handleFileUpload(e, key === 'backgroundImage' ? 'image' : 'video')
            }
            className="rounded w-full border bg-white p-2 text-gray-900 dark:bg-gray-700 dark:text-gray-100"
          />
          {styles.backgroundImage && (
            <button
              onClick={() => updateStyle('backgroundImage', '')}
              className="rounded mt-2 bg-red-500 px-2 py-1 text-white transition-colors hover:bg-red-600"
            >
              Clear Background Image
            </button>
          )}
          {styles.backgroundVideo && (
            <button
              onClick={() => updateStyle('backgroundVideo', '')}
              className="rounded mt-2 bg-red-500 px-2 py-1 text-white transition-colors hover:bg-red-600"
            >
              Clear Background Video
            </button>
          )}
        </>
      )}
    </div>
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70"
      style={{
        backgroundImage: styles.backgroundImage || undefined,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {styles.backgroundVideo && (
        <video
          className="absolute inset-0 z-[-1] h-full w-full object-cover"
          src={styles.backgroundVideo}
          autoPlay
          loop
          muted
        />
      )}
      <div className="scrollbar-hide max-h-[90vh] w-96 overflow-y-auto rounded-lg bg-white/80 p-6 shadow-lg backdrop-blur-md dark:bg-gray-800/70">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">
            Customize Theme
          </h2>
          <button
            onClick={onClose}
            className="rounded-full p-2 transition-colors duration-200 hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            <X size={20} />
          </button>
        </div>

        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Preset Themes
          </label>
          <select
            onChange={(e) =>
              setStyles(
                presetThemes[e.target.value as keyof typeof presetThemes],
              )
            }
            className="rounded w-full border bg-white p-2 text-gray-900 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="">Custom</option>
            {Object.keys(presetThemes).map((theme) => (
              <option key={theme} value={theme}>
                {theme.charAt(0).toUpperCase() + theme.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-4">
          {renderControl('Background Color', 'bgColor', 'color')}
          {renderControl('Text Color', 'textColor', 'color')}
          {renderControl('Accent Color', 'activeBackgroundColor', 'color')}
          {renderControl('Icon Color', 'iconColor', 'color')}
          {renderControl('UI Background Color', 'uiBackgroundColor', 'color')}
          {renderControl('Sidebar Width', 'sidebarWidth', 'range', {
            min: 48,
            max: 128,
            step: 8,
          })}
          {renderControl('Icon Size', 'iconSize', 'range', {
            min: 16,
            max: 32,
            step: 2,
          })}
          {renderControl('Font Size', 'fontSize', 'range', {
            min: 12,
            max: 20,
            step: 1,
          })}
          {renderControl('Font Family', 'fontFamily', 'select', {
            choices: [
              'Inter, sans-serif',
              "'SF Pro Display', sans-serif",
              "'Roboto', sans-serif",
              "'Open Sans', sans-serif",
            ],
          })}
          {renderControl('Background Image', 'backgroundImage', 'file', {
            accept: 'image/*',
          })}
          {renderControl('Background Video', 'backgroundVideo', 'file', {
            accept: 'video/*',
          })}
        </div>
      </div>
    </div>
  );
};

export default CustomizationPopup;
