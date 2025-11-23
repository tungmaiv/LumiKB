import { Suspense } from 'react';
import { RegisterForm } from '@/components/auth/register-form';

function RegisterPageContent() {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Create an account</h2>
        <p className="text-sm text-muted-foreground">Enter your details to get started</p>
      </div>
      <RegisterForm />
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <RegisterPageContent />
    </Suspense>
  );
}
