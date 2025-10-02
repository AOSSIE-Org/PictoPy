// Type declarations for missing modules

declare module 'react' {
  import { ComponentType, ReactNode, CSSProperties } from 'react';
  
  export function useState<T>(initialState: T | (() => T)): [T, (value: T | ((prev: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: any[]): void;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: any[]): T;
  export function useMemo<T>(factory: () => T, deps: any[]): T;
  export function useRef<T>(initialValue: T): { current: T };
  
  export interface FormEvent<T = Element> {
    preventDefault(): void;
    stopPropagation(): void;
    currentTarget: T;
    target: EventTarget;
  }
  
  export interface ChangeEvent<T = Element> extends FormEvent<T> {
    target: EventTarget & T;
  }
  
  export interface MouseEvent<T = Element> extends FormEvent<T> {}
  
  export interface HTMLAttributes<T> {
    className?: string;
    id?: string;
    style?: CSSProperties;
    onClick?: (event: MouseEvent<T>) => void;
    children?: ReactNode;
  }
  
  export interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
    value?: string | number;
    placeholder?: string;
    onChange?: (event: ChangeEvent<T>) => void;
    type?: string;
  }
  
  export interface TextareaHTMLAttributes<T> extends HTMLAttributes<T> {
    value?: string;
    placeholder?: string;
    onChange?: (event: ChangeEvent<T>) => void;
    rows?: number;
  }
  
  export interface FormHTMLAttributes<T> extends HTMLAttributes<T> {
    onSubmit?: (event: FormEvent<T>) => void;
  }
  
  export interface ButtonHTMLAttributes<T> extends HTMLAttributes<T> {
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
  }
  
  export default React;
}

declare module 'react-dom' {
  import * as ReactDOM from 'react-dom';
  export = ReactDOM;
}

declare module 'react-redux' {
  export function useSelector<T>(selector: (state: any) => T): T;
  export function useDispatch(): any;
  export function connect(mapStateToProps?: any, mapDispatchToProps?: any): any;
  export const Provider: any;
}

declare module 'lucide-react' {
  import { ComponentType, SVGProps } from 'react';
  
  export interface LucideProps extends Partial<Omit<SVGProps<SVGSVGElement>, "ref">> {
    size?: string | number;
    absoluteStrokeWidth?: boolean;
  }
  
  export type Icon = ComponentType<LucideProps>;
  
  export const Check: Icon;
  export const Heart: Icon;
  export const Share2: Icon;
  export const Eye: Icon;
  export const EyeOff: Icon;
  export const Lock: Icon;
  export const Search: Icon;
  export const X: Icon;
  export const FolderPlus: Icon;
  export const Trash2: Icon;
  export const Download: Icon;
  export const SelectAll: Icon;
  export const RotateCcw: Icon;
  export const CheckSquare: Icon;
  export const ArrowLeft: Icon;
  export const Settings: Icon;
  export const Users: Icon;
  export const Calendar: Icon;
  export const Edit3: Icon;
  export const MoreHorizontal: Icon;
  export const Plus: Icon;
  export const FolderOpen: Icon;
  export const ImageIcon: Icon;
}

declare module '@tauri-apps/api/core' {
  export function convertFileSrc(filePath: string, protocol?: string): string;
  export function invoke(cmd: string, args?: Record<string, unknown>): Promise<any>;
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module 'react/jsx-dev-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

// Global JSX namespace
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
    
    interface Element extends React.ReactElement<any, any> { }
    
    interface ElementClass extends React.Component<any> {
      render(): React.ReactNode;
    }
    
    interface ElementAttributesProperty {
      props: {};
    }
    
    interface ElementChildrenAttribute {
      children: {};
    }
    
    interface IntrinsicAttributes extends React.Attributes { }
    interface IntrinsicClassAttributes<T> extends React.ClassAttributes<T> { }
  }
}