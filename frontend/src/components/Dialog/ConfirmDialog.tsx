import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

export interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  onConfirm: () => void | Promise<void>;
  destructive?: boolean;
  /** Offers the caller an extra choice alongside the confirmation. */
  checkboxLabel?: string;
  checkboxChecked?: boolean;
  onCheckboxChange?: (checked: boolean) => void;
  /** Spells out what the current checkbox state will actually do. */
  checkboxHint?: string;
  checkboxHintDestructive?: boolean;
  /** "Don't show again" checkbox, rendered on the left of the footer buttons. Omit onDontShowAgainChange to leave it out entirely. */
  dontShowAgainLabel?: string;
  dontShowAgainChecked?: boolean;
  onDontShowAgainChange?: (checked: boolean) => void;
}

interface DialogCheckboxProps {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  hint?: string;
  hintDestructive?: boolean;
  /** Renders as a bordered option card instead of a plain inline row. */
  card?: boolean;
}

/** Shared checkbox + label (+ optional hint) row, reused for both the body option and the footer's "don't show again". */
const DialogCheckbox: React.FC<DialogCheckboxProps> = ({
  id,
  label,
  checked,
  onChange,
  hint,
  hintDestructive,
  card,
}) => (
  <div
    className={`flex gap-3 ${hint ? 'items-start' : 'items-center'} ${
      card ? 'rounded-xl border border-border/60 p-4 transition-colors hover:border-border' : ''
    }`}
  >
    <input
      id={id}
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      className="accent-primary mt-0.5 h-4 w-4 cursor-pointer"
    />
    <div className="space-y-1">
      <Label htmlFor={id} className={`cursor-pointer ${card ? 'text-sm font-medium' : 'text-sm'}`}>
        {label}
      </Label>
      {hint && (
        <p
          className={
            hintDestructive
              ? 'text-destructive text-sm leading-relaxed'
              : 'text-muted-foreground text-sm leading-relaxed'
          }
        >
          {hint}
        </p>
      )}
    </div>
  </div>
);

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel = 'Cancel',
  onConfirm,
  destructive = true,
  checkboxLabel,
  checkboxChecked = false,
  onCheckboxChange,
  checkboxHint,
  checkboxHintDestructive,
  dontShowAgainLabel = "Don't show again",
  dontShowAgainChecked = false,
  onDontShowAgainChange,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full !max-w-[520px] rounded-2xl p-7">
        <DialogHeader className="space-y-3">
          <span
            className={`flex h-11 w-11 items-center justify-center rounded-full ${
              destructive ? 'bg-destructive/10 text-destructive' : 'bg-primary/10 text-primary'
            }`}
          >
            {destructive ? (
              <AlertTriangle className="h-5 w-5" />
            ) : (
              <Info className="h-5 w-5" />
            )}
          </span>
          <DialogTitle className="text-xl font-semibold">{title}</DialogTitle>
          <DialogDescription className="text-sm leading-relaxed">
            {description}
          </DialogDescription>
        </DialogHeader>

        {checkboxLabel && (
          <DialogCheckbox
            id="confirm-dialog-checkbox"
            label={checkboxLabel}
            checked={checkboxChecked}
            onChange={onCheckboxChange ?? (() => {})}
            hint={checkboxHint}
            hintDestructive={checkboxHintDestructive}
            card
          />
        )}

        <DialogFooter
          className={onDontShowAgainChange ? 'sm:justify-between' : undefined}
        >
          {onDontShowAgainChange && (
            <DialogCheckbox
              id="confirm-dialog-dont-show-again"
              label={dontShowAgainLabel}
              checked={dontShowAgainChecked}
              onChange={onDontShowAgainChange}
            />
          )}
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              {cancelLabel}
            </Button>
            <Button
              onClick={async () => {
                await onConfirm();
                onOpenChange(false);
              }}
              variant={destructive ? 'destructive' : 'default'}
            >
              {confirmLabel}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};