'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { LoginForm } from '@/components/auth/login-form';

function LoginPageContent() {
  const searchParams = useSearchParams();
  const redirect = searchParams.get('redirect');
  const redirectTo = redirect ? decodeURIComponent(redirect) : '/';

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Welcome back</h2>
        <p className="text-sm text-muted-foreground">Sign in to your account to continue</p>
      </div>
      <LoginForm redirectTo={redirectTo} />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginPageContent />
    </Suspense>
  );
}
