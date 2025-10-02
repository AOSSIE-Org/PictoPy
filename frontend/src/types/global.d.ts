// Global React types to help with JSX and hooks

import { CSSProperties } from 'react';

declare global {
  const React: {
    useState: <T>(initialState: T | (() => T)) => [T, (value: T | ((prev: T) => T)) => void];
    useEffect: (effect: () => void | (() => void), deps?: any[]) => void;
    useCallback: <T extends (...args: any[]) => any>(callback: T, deps: any[]) => T;
    useMemo: <T>(factory: () => T, deps: any[]) => T;
    useRef: <T>(initialValue: T) => { current: T };
    Fragment: any;
    Component: any;
    PureComponent: any;
    createElement: any;
  };
  
  namespace React {
    type ReactNode = any;
    type ComponentType<P = {}> = any;
    type Key = string | number;
    
    interface CSSProperties {
      [key: string]: any;
    }
    
    interface FormEvent<T = Element> {
      preventDefault(): void;
      stopPropagation(): void;
      currentTarget: T;
      target: EventTarget & { value?: string };
    }
    
    interface ChangeEvent<T = Element> extends FormEvent<T> {}
    interface MouseEvent<T = Element> extends FormEvent<T> {}
    
    interface HTMLAttributes<T> {
      className?: string;
      id?: string;
      style?: CSSProperties;
      onClick?: (event: MouseEvent<T>) => void;
      children?: ReactNode;
      key?: Key;
    }
    
    interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
      value?: string | number;
      placeholder?: string;
      onChange?: (event: ChangeEvent<T>) => void;
      type?: string;
    }
    
    interface TextareaHTMLAttributes<T> extends HTMLAttributes<T> {
      value?: string;
      placeholder?: string;
      onChange?: (event: ChangeEvent<T>) => void;
      rows?: number;
    }
    
    interface FormHTMLAttributes<T> extends HTMLAttributes<T> {
      onSubmit?: (event: FormEvent<T>) => void;
    }
  }
}

export {};