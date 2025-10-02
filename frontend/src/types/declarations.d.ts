// React type declarations for when @types/react is not available
declare module 'react' {
  export interface Component {
    render(): JSX.Element | null;
  }

  export function useState<T>(
    initialState: T | (() => T),
  ): [T, (value: T | ((prev: T) => T)) => void];
  export function useEffect(
    effect: () => void | (() => void),
    deps?: any[],
  ): void;
  export function useCallback<T extends (...args: any[]) => any>(
    callback: T,
    deps: any[],
  ): T;
  export function useMemo<T>(factory: () => T, deps: any[]): T;
  export function useRef<T>(initialValue: T): { current: T };
  export function useContext<T>(context: Context<T>): T;

  export interface Context<T> {
    Provider: ComponentType<{ value: T; children?: ReactNode }>;
    Consumer: ComponentType<{ children: (value: T) => ReactNode }>;
  }

  export function createContext<T>(defaultValue: T): Context<T>;

  export type ReactNode =
    | JSX.Element
    | string
    | number
    | boolean
    | null
    | undefined
    | ReactNode[];
  export type ComponentType<P = {}> = (props: P) => JSX.Element | null;
  export type Key = string | number;

  export interface ReactElement<P = any> {
    type: string | ComponentType<P>;
    props: P;
    key: Key | null;
  }

  export interface FormEvent<T = Element> {
    preventDefault(): void;
    target: T;
  }

  export interface ChangeEvent<T = Element> {
    target: T & { value: string };
  }

  export interface MouseEvent<T = Element> {
    target: T;
    stopPropagation(): void;
    preventDefault(): void;
  }

  export namespace React {
    export type FormEvent<T = Element> = import('react').FormEvent<T>;
    export type ChangeEvent<T = Element> = import('react').ChangeEvent<T>;
    export type MouseEvent<T = Element> = import('react').MouseEvent<T>;
  }
}

declare module 'react-dom' {
  export function render(element: JSX.Element, container: Element): void;
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
}

// React Redux types
declare module 'react-redux' {
  export function useSelector<T>(selector: (state: any) => T): T;
  export function useDispatch(): any;
  export const Provider: any;
}

// Lucide React types
declare module 'lucide-react' {
  export const ArrowLeft: any;
  export const Check: any;
  export const CheckSquare: any;
  export const Download: any;
  export const Edit3: any;
  export const Eye: any;
  export const EyeOff: any;
  export const FolderOpen: any;
  export const FolderPlus: any;
  export const Heart: any;
  export const Lock: any;
  export const MoreHorizontal: any;
  export const Plus: any;
  export const RotateCcw: any;
  export const Search: any;
  export const SelectAll: any;
  export const Settings: any;
  export const Share: any;
  export const Share2: any;
  export const Trash2: any;
  export const Users: any;
  export const X: any;
}

// JSX namespace for intrinsic elements
declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

// Tauri API declarations
declare module '@tauri-apps/api/core' {
  export function convertFileSrc(filePath: string, protocol?: string): string;
  export function invoke(
    cmd: string,
    args?: Record<string, unknown>,
  ): Promise<any>;
}
