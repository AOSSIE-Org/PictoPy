import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80 focus:ring-primary dark:bg-primary-dark dark:text-primary-foreground-dark dark:hover:bg-primary-dark/90 dark:active:bg-primary-dark/80',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/80 focus:ring-destructive dark:bg-destructive-dark dark:text-destructive-foreground-dark dark:hover:bg-destructive-dark/90 dark:active:bg-destructive-dark/80',
        outline:
          'border border-input hover:bg-accent hover:text-accent-foreground active:bg-accent/90 focus:ring-accent dark:bg-accent-dark dark:text-accent-foreground-dark dark:border-input-dark',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80 active:bg-secondary/70 focus:ring-secondary dark:bg-secondary-dark dark:text-secondary-foreground-dark dark:hover:bg-secondary-dark/80 dark:active:bg-secondary-dark/70',
        ghost:
          'hover:bg-accent hover:text-accent-foreground active:bg-accent/90 focus:ring-accent dark:hover:bg-accent-dark dark:text-accent-foreground-dark',
        link:
          'text-primary underline-offset-4 hover:underline active:text-primary/80 focus:ring-primary dark:text-primary-dark dark:hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);

Button.displayName = 'Button';

export { Button, buttonVariants };
