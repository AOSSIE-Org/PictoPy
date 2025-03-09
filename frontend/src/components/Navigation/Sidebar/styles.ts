export interface CustomStyles {
  bgColor: string;
  textColor: string;
  borderColor: string;
  iconSize: number;
  sidebarWidth: number;
  borderRadius: number;
  fontFamily: string;
  fontSize: number;
  hoverBackgroundColor: string;
  activeBackgroundColor: string;
  activeTextColor: string;
  iconColor: string;
  uiBackgroundColor: string;
  backgroundImage: string;
  backgroundVideo: string;
}

export const defaultStyles: CustomStyles = {
  bgColor: '#1f2937',
  textColor: '#f3f4f6',
  borderColor: '#374151',
  iconSize: 20,
  sidebarWidth: 128,
  borderRadius: 8,
  fontFamily: 'SF Pro Display, sans-serif',
  fontSize: 14,
  hoverBackgroundColor: '#374151',
  activeBackgroundColor: '#4b5563',
  activeTextColor: '#ffffff',
  iconColor: '#9ca3af',
  uiBackgroundColor: '#111827',
  backgroundImage: '',
  backgroundVideo: '',
};

export const presetThemes = {
  dark: { ...defaultStyles },
  light: {
    ...defaultStyles,
    bgColor: '#ffffff',
    textColor: '#333333',
    borderColor: '#e5e7eb',
    hoverBackgroundColor: '#f3f4f6',
    activeBackgroundColor: '#e5e7eb',
    activeTextColor: '#000000',
    iconColor: '#4b5563',
    uiBackgroundColor: '#f0f2f5',
    fontFamily: 'Inter, sans-serif',
  },
  blue: {
    ...defaultStyles,
    bgColor: '#e0f2fe',
    textColor: '#0c4a6e',
    borderColor: '#7dd3fc',
    hoverBackgroundColor: '#bae6fd',
    activeBackgroundColor: '#7dd3fc',
    activeTextColor: '#0c4a6e',
    iconColor: '#0369a1',
    uiBackgroundColor: '#f0f9ff',
    fontFamily: 'Roboto, sans-serif',
  },
};
