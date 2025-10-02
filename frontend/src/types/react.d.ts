/// <reference types="react" />
/// <reference types="react-dom" />

import * as React from 'react';

declare global {
  namespace React {
    interface HTMLAttributes<T> extends React.AriaAttributes, React.DOMAttributes<T> {
      // Common HTML attributes
      className?: string;
      id?: string;
      style?: React.CSSProperties;
      onClick?: React.MouseEventHandler<T>;
      onChange?: React.ChangeEventHandler<T>;
      onSubmit?: React.FormEventHandler<T>;
      children?: React.ReactNode;
      key?: React.Key;
    }
    
    interface SVGProps<T> extends SVGAttributes<T>, React.ClassAttributes<T> {}
    
    type FormEvent<T = Element> = React.SyntheticEvent<T, Event>;
    type ChangeEvent<T = Element> = React.SyntheticEvent<T, Event> & {
      target: EventTarget & T;
    };
    type MouseEvent<T = Element> = React.SyntheticEvent<T, Event>;
    
    interface FormEventHandler<T = Element> {
      (event: FormEvent<T>): void;
    }
    
    interface ChangeEventHandler<T = Element> {
      (event: ChangeEvent<T>): void;
    }
    
    interface MouseEventHandler<T = Element> {
      (event: MouseEvent<T>): void;
    }
  }
}

export {};