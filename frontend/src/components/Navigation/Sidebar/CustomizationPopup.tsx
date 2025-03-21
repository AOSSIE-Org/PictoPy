import React, { useState } from 'react';
import { X, Palette, Layout, Type, Image } from 'lucide-react';
import { CustomStyles, presetThemes, defaultStyles } from './styles';

// Define the props interface for the CustomizationPopup component
interface CustomizationPopupProps {
  styles: CustomStyles; // Current styles
  setStyles: React.Dispatch<React.SetStateAction<CustomStyles>>; // Function to update styles
  onClose: () => void; // Function to close the popup
}

type TabType = 'presets' | 'colors' | 'layout' | 'typography' | 'background';

const CustomizationPopup: React.FC<CustomizationPopupProps> = ({
  styles,
  setStyles,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('presets');

  const saveTheme = () => {
    localStorage.setItem('savedStyles', JSON.stringify(styles));
    alert('Theme saved successfully!');
  };

  // Function to reset styles to default
  const resetTheme = () => {
    setStyles(defaultStyles);
    localStorage.removeItem('savedStyles');
    alert('Theme reset to default!');
  };

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
   */
  const renderColorControl = (label: string, key: keyof CustomStyles) => (
    <div className="mb-4 flex items-center">
      <div className="relative mr-4">
        <input
          type="color"
          value={styles[key] as string}
          onChange={(e) => updateStyle(key, e.target.value)}
          className="h-10 w-10 cursor-pointer rounded-md border-2 border-gray-200 shadow-sm dark:border-gray-600"
        />
        <div
          className="rounded-full absolute -right-1 -top-1 h-4 w-4 border border-white shadow-sm"
          style={{ backgroundColor: styles[key] as string }}
        ></div>
      </div>
      <div className="flex-grow">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        <div className="rounded mt-1 bg-gray-100 px-2 py-1 font-mono text-xs dark:bg-gray-800">
          {styles[key]}
        </div>
      </div>
    </div>
  );

  const renderRangeControl = (
    label: string,
    key: keyof CustomStyles,
    options?: { min?: number; max?: number; step?: number },
  ) => (
    <div className="mb-4">
      <div className="mb-1 flex justify-between">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs dark:bg-gray-800">
          {styles[key]}
        </span>
      </div>
      <input
        type="range"
        min={options?.min}
        max={options?.max}
        step={options?.step}
        value={styles[key] as number}
        onChange={(e) => updateStyle(key, parseInt(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 dark:bg-gray-700"
      />
      <div className="mt-1 flex justify-between">
        <span className="text-xs text-gray-500">{options?.min}</span>
        <span className="text-xs text-gray-500">{options?.max}</span>
      </div>
    </div>
  );

  const renderSelectControl = (
    label: string,
    key: keyof CustomStyles,
    options?: { choices?: string[] },
  ) => (
    <div className="mb-4">
      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <select
        value={styles[key] as string}
        onChange={(e) => updateStyle(key, e.target.value)}
        className="w-full rounded-md border border-gray-300 bg-white p-2 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
      >
        {options?.choices?.map((choice) => (
          <option key={choice} value={choice}>
            {choice}
          </option>
        ))}
      </select>
    </div>
  );

  const renderFileControl = (
    label: string,
    key: keyof CustomStyles,
    options?: { accept?: string },
  ) => (
    <div className="mb-4">
      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <div className="flex flex-col">
        <label className="flex h-20 cursor-pointer appearance-none items-center justify-center rounded-md border-2 border-dashed border-gray-300 bg-white px-4 transition hover:border-gray-400 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600">
          <span className="flex items-center space-x-2">
            <Image size={18} />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {styles[key] ? 'Change file' : 'Upload file'}
            </span>
          </span>
          <input
            type="file"
            accept={options?.accept}
            onChange={(e) =>
              handleFileUpload(e, key === 'backgroundImage' ? 'image' : 'video')
            }
            className="hidden"
          />
        </label>

        {styles[key] && (
          <div className="mt-2 flex items-center justify-between rounded-md bg-gray-100 p-2 dark:bg-gray-700">
            <span className="max-w-[70%] truncate text-xs">
              {String(styles[key]).substring(0, 25)}...
            </span>
            <button
              onClick={() => updateStyle(key, '')}
              className="rounded bg-red-500 px-2 py-1 text-xs text-white transition-colors hover:bg-red-600"
            >
              Clear
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const TabButton: React.FC<{
    active: boolean;
    onClick: () => void;
    icon: React.ReactNode;
    label: string;
  }> = ({ active, onClick, icon, label }) => (
    <button
      onClick={onClick}
      className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
      }`}
    >
      <div
        className={`flex items-center justify-center ${active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`}
      >
        {icon}
      </div>
      <span className="ml-2">{label}</span>
    </button>
  );

  const SectionHeader: React.FC<{ title: string }> = ({ title }) => (
    <h3 className="mb-4 border-b border-gray-200 pb-2 text-sm font-semibold uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-gray-400">
      {title}
    </h3>
  );

  const renderPresetThemes = () => (
    <div>
      <SectionHeader title="Theme Presets" />
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(presetThemes).map(([name, theme]) => (
          <button
            key={name}
            onClick={() => setStyles(theme)}
            className={`rounded-lg border-2 p-3 transition-all ${
              JSON.stringify(styles) === JSON.stringify(theme)
                ? 'border-blue-500 shadow-md'
                : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
            }`}
          >
            <div
              className="relative mb-2 flex h-12 items-center justify-center overflow-hidden rounded-md"
              style={{
                backgroundColor: theme.bgColor,
                boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.1)',
              }}
            >
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage:
                    'linear-gradient(45deg, #ddd 25%, transparent 25%, transparent 75%, #ddd 75%, #ddd), linear-gradient(45deg, #ddd 25%, transparent 25%, transparent 75%, #ddd 75%, #ddd)',
                  backgroundSize: '8px 8px',
                  backgroundPosition: '0 0, 4px 4px',
                }}
              ></div>
              <div
                className="rounded-full relative z-10 p-2"
                style={{
                  backgroundColor: theme.activeBackgroundColor,
                  color: theme.activeTextColor,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                }}
              >
                <Palette size={18} />
              </div>
            </div>
            <p className="text-center text-sm font-medium">
              {name.charAt(0).toUpperCase() + name.slice(1)}
            </p>
          </button>
        ))}
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'presets':
        return renderPresetThemes();
      case 'colors':
        return (
          <div>
            <SectionHeader title="Color Scheme" />
            {renderColorControl('Background Color', 'bgColor')}
            {renderColorControl('Text Color', 'textColor')}
            {renderColorControl('Accent Color', 'activeBackgroundColor')}
            {renderColorControl('Active Text Color', 'activeTextColor')}
            {renderColorControl('Icon Color', 'iconColor')}
            {renderColorControl('UI Background', 'uiBackgroundColor')}
          </div>
        );
      case 'layout':
        return (
          <div>
            <SectionHeader title="Layout Settings" />
            {renderRangeControl('Sidebar Width', 'sidebarWidth', {
              min: 48,
              max: 128,
              step: 8,
            })}
            {renderRangeControl('Icon Size', 'iconSize', {
              min: 16,
              max: 32,
              step: 2,
            })}
          </div>
        );
      case 'typography':
        return (
          <div>
            <SectionHeader title="Typography" />
            {renderRangeControl('Font Size', 'fontSize', {
              min: 12,
              max: 20,
              step: 1,
            })}
            {renderSelectControl('Font Family', 'fontFamily', {
              choices: [
                'Inter, sans-serif',
                "'SF Pro Display', sans-serif",
                "'Roboto', sans-serif",
                "'Open Sans', sans-serif",
              ],
            })}
          </div>
        );
      case 'background':
        return (
          <div>
            <SectionHeader title="Background Media" />
            {renderFileControl('Background Image', 'backgroundImage', {
              accept: 'image/*',
            })}
            {renderFileControl('Background Video', 'backgroundVideo', {
              accept: 'video/*',
            })}
          </div>
        );
      default:
        return <div>Select a tab</div>;
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm"
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
      <div className="rounded-xl max-h-[85vh] w-[450px] overflow-hidden bg-white/90 shadow-2xl backdrop-blur-md dark:bg-gray-800/90">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">
            Customize Theme
          </h2>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex items-center space-x-1 overflow-x-auto border-b border-gray-200 px-4 py-2 dark:border-gray-700">
          <TabButton
            active={activeTab === 'presets'}
            onClick={() => setActiveTab('presets')}
            icon={<Palette size={16} />}
            label="Presets"
          />
          <TabButton
            active={activeTab === 'colors'}
            onClick={() => setActiveTab('colors')}
            icon={
              <div className="rounded-full h-4 w-4 overflow-hidden border border-gray-300 dark:border-gray-500">
                <div className="h-full w-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
              </div>
            }
            label="Colors"
          />
          <TabButton
            active={activeTab === 'layout'}
            onClick={() => setActiveTab('layout')}
            icon={<Layout size={16} />}
            label="Layout"
          />
          <TabButton
            active={activeTab === 'typography'}
            onClick={() => setActiveTab('typography')}
            icon={<Type size={16} />}
            label="Typography"
          />
          <TabButton
            active={activeTab === 'background'}
            onClick={() => setActiveTab('background')}
            icon={<Image size={16} />}
            label="Background"
          />
        </div>

        <div className="scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 max-h-[calc(85vh-120px)] overflow-y-auto p-6">
          {renderTabContent()}
        </div>
        <div className="flex justify-between p-8">
          <button
            onClick={saveTheme}
            className="animation duration-400 rounded-[6px] bg-white p-3 text-black hover:cursor-pointer hover:bg-gray-200"
          >
            Save theme
          </button>

          <button
            onClick={resetTheme}
            className="animation duration-400 rounded-[6px] bg-white p-3 text-black hover:cursor-pointer hover:bg-gray-200"
          >
            Reset theme
          </button>
        </div>
      </div>
    </div>
  );
};

export default CustomizationPopup;
