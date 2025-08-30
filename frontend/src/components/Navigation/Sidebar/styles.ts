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
  bgColor: '#111827',
  textColor: '#f9fafb',
  borderColor: '#374151',
  iconSize: 20,
  sidebarWidth: 128,
  borderRadius: 12,
  fontFamily: 'SF Pro Display, system-ui, sans-serif',
  fontSize: 14,
  hoverBackgroundColor: '#2d3748',
  activeBackgroundColor: '#3b82f6',
  activeTextColor: '#ffffff',
  iconColor: '#9ca3af',
  uiBackgroundColor: '#0f172a',
  backgroundImage: '',
  backgroundVideo: '',
};

export const presetThemes = {
  dark: { ...defaultStyles },
  light: {
    ...defaultStyles,
    bgColor: '#ffffff',
    textColor: '#111827',
    borderColor: '#e5e7eb',
    hoverBackgroundColor: '#f3f4f6',
    activeBackgroundColor: '#3b82f6',
    activeTextColor: '#ffffff',
    iconColor: '#4b5563',
    uiBackgroundColor: '#f8fafc',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  blue: {
    ...defaultStyles,
    bgColor: '#ecf0ff',
    textColor: '#1e3a8a',
    borderColor: '#93c5fd',
    hoverBackgroundColor: '#bfdbfe',
    activeBackgroundColor: '#3b82f6',
    activeTextColor: '#ffffff',
    iconColor: '#1e40af',
    uiBackgroundColor: '#f1f5f9',
    fontFamily: 'Roboto, system-ui, sans-serif',
  },
};
