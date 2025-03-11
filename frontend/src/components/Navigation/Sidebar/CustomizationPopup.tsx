import React, { useState } from 'react';
import { X, Palette, Layout, Type, Image } from 'lucide-react';
import { CustomStyles, presetThemes } from './styles';

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
          className="absolute -right-1 -top-1 h-4 w-4 rounded-full border border-white shadow-sm"
          style={{ backgroundColor: styles[key] as string }}
        ></div>
      </div>
      <div className="flex-grow">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        <div className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 mt-1 rounded">
          {styles[key]}
        </div>
      </div>
    </div>
  );

  const renderRangeControl = (
    label: string,
    key: keyof CustomStyles,
    options?: { min?: number; max?: number; step?: number }
  ) => (
    <div className="mb-4">
      <div className="flex justify-between mb-1">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        <span className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
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
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
      />
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-500">{options?.min}</span>
        <span className="text-xs text-gray-500">{options?.max}</span>
      </div>
    </div>
  );

  const renderSelectControl = (
    label: string,
    key: keyof CustomStyles,
    options?: { choices?: string[] }
  ) => (
    <div className="mb-4">
      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <select
        value={styles[key] as string}
        onChange={(e) => updateStyle(key, e.target.value)}
        className="w-full p-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
    options?: { accept?: string }
  ) => (
    <div className="mb-4">
      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <div className="flex flex-col">
        <label className="flex items-center justify-center h-20 px-4 transition bg-white border-2 border-gray-300 border-dashed rounded-md appearance-none cursor-pointer hover:border-gray-400 focus:outline-none dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600">
          <span className="flex items-center space-x-2">
            <Image size={18} />
            <span className="font-medium text-sm text-gray-600 dark:text-gray-400">
              {styles[key] ? "Change file" : "Upload file"}
            </span>
          </span>
          <input
            type="file"
            accept={options?.accept}
            onChange={(e) => handleFileUpload(e, key === 'backgroundImage' ? 'image' : 'video')}
            className="hidden"
          />
        </label>
        
        {styles[key] && (
          <div className="mt-2 flex items-center justify-between bg-gray-100 dark:bg-gray-700 p-2 rounded-md">
            <span className="text-xs truncate max-w-[70%]">{String(styles[key]).substring(0, 25)}...</span>
            <button
              onClick={() => updateStyle(key, '')}
              className="text-xs bg-red-500 hover:bg-red-600 text-white py-1 px-2 rounded transition-colors"
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
      className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        active
          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
          : 'hover:bg-gray-100 text-gray-700 dark:hover:bg-gray-700 dark:text-gray-300'
      }`}
    >
      {icon}
      <span className="ml-2">{label}</span>
    </button>
  );

  const SectionHeader: React.FC<{ title: string }> = ({ title }) => (
    <h3 className="text-sm uppercase tracking-wider font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 pb-2 mb-4">
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
            className={`p-3 rounded-lg border-2 transition-all ${
              JSON.stringify(styles) === JSON.stringify(theme)
                ? 'border-blue-500 shadow-md'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-center justify-center h-12 rounded-md mb-2" style={{ 
              backgroundColor: theme.bgColor,
              color: theme.textColor
            }}>
              <div style={{ color: theme.iconColor }}>
                <Palette size={18} />
              </div>
            </div>
            <p className="text-sm font-medium text-center">
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
      <div className="w-[450px] max-h-[85vh] bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">
            Customize Theme
          </h2>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="flex items-center space-x-1 overflow-x-auto px-4 py-2 border-b border-gray-200 dark:border-gray-700">
          <TabButton 
            active={activeTab === 'presets'} 
            onClick={() => setActiveTab('presets')}
            icon={<Palette size={16} />}
            label="Presets"
          />
          <TabButton 
            active={activeTab === 'colors'} 
            onClick={() => setActiveTab('colors')}
            icon={<span className="w-4 h-4 rounded-full bg-gradient-to-r from-blue-500 to-purple-500" />}
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
        
        <div className="p-6 overflow-y-auto max-h-[calc(85vh-120px)] scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default CustomizationPopup;
