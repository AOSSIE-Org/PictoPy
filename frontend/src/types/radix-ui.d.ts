// Type declaration for @radix-ui/react-dropdown-menu
// This is a workaround for TypeScript module resolution issues

declare module '@radix-ui/react-dropdown-menu' {
  import * as React from 'react';

  export interface DropdownMenuProps {
    children?: React.ReactNode;
    open?: boolean;
    defaultOpen?: boolean;
    onOpenChange?: (open: boolean) => void;
    modal?: boolean;
  }

  export interface DropdownMenuTriggerProps {
    children?: React.ReactNode;
    asChild?: boolean;
  }

  export interface DropdownMenuContentProps {
    children?: React.ReactNode;
    className?: string;
    sideOffset?: number;
    align?: 'start' | 'center' | 'end';
    side?: 'top' | 'right' | 'bottom' | 'left';
    alignOffset?: number;
    avoidCollisions?: boolean;
    collisionBoundary?: Element | Element[];
    collisionPadding?:
      | number
      | Partial<Record<'top' | 'right' | 'bottom' | 'left', number>>;
    sticky?: 'partial' | 'always';
    hideWhenDetached?: boolean;
    forceMount?: boolean;
    loop?: boolean;
    onCloseAutoFocus?: (event: Event) => void;
    onEscapeKeyDown?: (event: KeyboardEvent) => void;
    onPointerDownOutside?: (event: Event) => void;
    onFocusOutside?: (event: Event) => void;
    onInteractOutside?: (event: Event) => void;
  }

  export interface DropdownMenuItemProps {
    children?: React.ReactNode;
    className?: string;
    disabled?: boolean;
    onSelect?: (event: Event) => void;
    onClick?: () => void;
    textValue?: string;
    asChild?: boolean;
  }

  export interface DropdownMenuCheckboxItemProps extends DropdownMenuItemProps {
    checked?: boolean | 'indeterminate';
    onCheckedChange?: (checked: boolean) => void;
  }

  export interface DropdownMenuRadioItemProps extends DropdownMenuItemProps {
    value: string;
  }

  export interface DropdownMenuLabelProps {
    children?: React.ReactNode;
    className?: string;
    asChild?: boolean;
  }

  export interface DropdownMenuSeparatorProps {
    className?: string;
  }

  export interface DropdownMenuGroupProps {
    children?: React.ReactNode;
  }

  export interface DropdownMenuPortalProps {
    children?: React.ReactNode;
    forceMount?: boolean;
    container?: HTMLElement;
  }

  export interface DropdownMenuSubProps {
    children?: React.ReactNode;
    open?: boolean;
    defaultOpen?: boolean;
    onOpenChange?: (open: boolean) => void;
  }

  export interface DropdownMenuSubTriggerProps {
    children?: React.ReactNode;
    className?: string;
    disabled?: boolean;
    textValue?: string;
    asChild?: boolean;
  }

  export interface DropdownMenuSubContentProps {
    children?: React.ReactNode;
    className?: string;
    sideOffset?: number;
    alignOffset?: number;
    forceMount?: boolean;
    loop?: boolean;
  }

  export interface DropdownMenuRadioGroupProps {
    children?: React.ReactNode;
    value?: string;
    onValueChange?: (value: string) => void;
  }

  export interface DropdownMenuItemIndicatorProps {
    children?: React.ReactNode;
    className?: string;
    forceMount?: boolean;
  }

  export const Root: React.FC<DropdownMenuProps>;
  export const Trigger: React.ForwardRefExoticComponent<DropdownMenuTriggerProps>;
  export const Portal: React.FC<DropdownMenuPortalProps>;
  export const Content: React.ForwardRefExoticComponent<DropdownMenuContentProps>;
  export const Group: React.FC<DropdownMenuGroupProps>;
  export const Item: React.ForwardRefExoticComponent<DropdownMenuItemProps>;
  export const CheckboxItem: React.ForwardRefExoticComponent<DropdownMenuCheckboxItemProps>;
  export const RadioGroup: React.FC<DropdownMenuRadioGroupProps>;
  export const RadioItem: React.ForwardRefExoticComponent<DropdownMenuRadioItemProps>;
  export const ItemIndicator: React.ForwardRefExoticComponent<DropdownMenuItemIndicatorProps>;
  export const Label: React.ForwardRefExoticComponent<DropdownMenuLabelProps>;
  export const Separator: React.ForwardRefExoticComponent<DropdownMenuSeparatorProps>;
  export const Sub: React.FC<DropdownMenuSubProps>;
  export const SubTrigger: React.ForwardRefExoticComponent<DropdownMenuSubTriggerProps>;
  export const SubContent: React.ForwardRefExoticComponent<DropdownMenuSubContentProps>;
  export const Close: React.ForwardRefExoticComponent<{
    children?: React.ReactNode;
    asChild?: boolean;
  }>;
}
