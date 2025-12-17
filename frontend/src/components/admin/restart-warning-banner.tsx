/**
 * Warning banner displayed when config changes require service restart.
 */

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertTriangle, X } from 'lucide-react';

interface RestartWarningBannerProps {
  changedKeys: string[];
  onDismiss: () => void;
}

export function RestartWarningBanner({ changedKeys, onDismiss }: RestartWarningBannerProps) {
  if (changedKeys.length === 0) return null;

  return (
    <Alert variant="default" className="bg-amber-50 border-amber-200 mb-6">
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-900">Service Restart Required</AlertTitle>
      <AlertDescription className="text-amber-800">
        {changedKeys.length === 1 ? (
          <p>
            Configuration setting <strong>{changedKeys[0]}</strong> has been changed. A service
            restart is required for this change to take effect.
          </p>
        ) : (
          <div>
            <p className="mb-2">
              {changedKeys.length} configuration settings have been changed and require a service
              restart:
            </p>
            <ul className="list-disc list-inside">
              {changedKeys.map((key) => (
                <li key={key}>{key}</li>
              ))}
            </ul>
          </div>
        )}
      </AlertDescription>
      <Button variant="ghost" size="sm" className="absolute top-2 right-2" onClick={onDismiss}>
        <X className="h-4 w-4" />
      </Button>
    </Alert>
  );
}
