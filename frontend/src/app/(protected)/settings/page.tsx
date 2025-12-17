'use client';

import { Settings, Construction } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

/**
 * Settings Page - Placeholder for future settings functionality
 *
 * AC-5.17.4: Settings link navigates to /settings (placeholder page)
 *
 * Future enhancements:
 * - User profile settings
 * - Notification preferences
 * - Tutorial restart option (Story 5.7 AC-5.7.6)
 * - Account management
 */
export default function SettingsPage(): React.ReactElement {
  const router = useRouter();

  return (
    <div className="container mx-auto max-w-2xl py-8 px-4">
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <Settings className="h-8 w-8" />
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>
        <p className="text-muted-foreground mt-1">
          Manage your account and application preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Construction className="h-5 w-5 text-muted-foreground" />
            Coming Soon
          </CardTitle>
          <CardDescription>Settings functionality is currently under development</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            We&apos;re working on bringing you a comprehensive settings experience. This will
            include:
          </p>
          <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
            <li>Profile management</li>
            <li>Notification preferences</li>
            <li>Appearance settings</li>
            <li>Tutorial restart option</li>
          </ul>
          <div className="pt-4">
            <Button variant="outline" onClick={() => router.back()}>
              Go Back
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
