import { Card, CardContent, CardHeader } from '@/components/ui/card';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4 py-12">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-2 text-center">
          <div className="mb-2">
            <h1 className="text-2xl font-bold text-primary">LumiKB</h1>
            <p className="text-sm text-muted-foreground">Knowledge Base Management</p>
          </div>
        </CardHeader>
        <CardContent>{children}</CardContent>
      </Card>
    </div>
  );
}
