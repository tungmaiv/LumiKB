/**
 * Modal for editing a system configuration setting.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ConfigSetting } from '@/types/config';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

interface EditConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  setting: ConfigSetting | null;
  onSave: (key: string, value: number | boolean | string) => Promise<void>;
  isSaving: boolean;
}

export function EditConfigModal({
  isOpen,
  onClose,
  setting,
  onSave,
  isSaving,
}: EditConfigModalProps) {
  const [value, setValue] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Reset value when setting changes
  if (setting && value === '') {
    setValue(String(setting.value));
  }

  const handleSave = async () => {
    if (!setting) return;

    setError(null);

    try {
      // Parse value based on data type
      let parsedValue: number | boolean | string;

      switch (setting.data_type) {
        case 'integer':
          parsedValue = parseInt(value, 10);
          if (isNaN(parsedValue)) {
            setError('Please enter a valid integer');
            return;
          }
          // Validate range
          if (setting.min_value !== undefined && parsedValue < setting.min_value) {
            setError(`Value must be at least ${setting.min_value}`);
            return;
          }
          if (setting.max_value !== undefined && parsedValue > setting.max_value) {
            setError(`Value must be at most ${setting.max_value}`);
            return;
          }
          break;

        case 'float':
          parsedValue = parseFloat(value);
          if (isNaN(parsedValue)) {
            setError('Please enter a valid number');
            return;
          }
          break;

        case 'boolean':
          parsedValue = value.toLowerCase() === 'true' || value === '1';
          break;

        case 'string':
          parsedValue = value;
          break;

        default:
          parsedValue = value;
      }

      await onSave(setting.key, parsedValue);
      setValue('');
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save setting');
    }
  };

  const handleClose = () => {
    setValue('');
    setError(null);
    onClose();
  };

  if (!setting) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit {setting.name}</DialogTitle>
          <DialogDescription>{setting.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="value">Value</Label>
            <Input
              id="value"
              type={
                setting.data_type === 'integer' || setting.data_type === 'float' ? 'number' : 'text'
              }
              value={value}
              onChange={(e) => setValue(e.target.value)}
              disabled={isSaving}
            />
            {setting.min_value !== undefined && setting.max_value !== undefined && (
              <p className="text-sm text-muted-foreground mt-1">
                Allowed range: {setting.min_value} - {setting.max_value}
              </p>
            )}
          </div>

          {setting.requires_restart && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Changing this setting requires a service restart to take effect.
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
