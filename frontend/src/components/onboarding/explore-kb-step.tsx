import { FolderOpen } from 'lucide-react';

export function ExploreKBStep() {
  return (
    <div className="flex flex-col items-center space-y-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/20">
        <FolderOpen className="h-8 w-8 text-blue-600 dark:text-blue-400" />
      </div>

      <div className="space-y-3 text-center">
        <h2 className="text-2xl font-bold">Explore the Sample Knowledge Base</h2>
        <p className="text-muted-foreground max-w-md">
          We&apos;ve pre-loaded a demo Knowledge Base with sample documents so you can see LumiKB in
          action right away.
        </p>
      </div>

      <div className="w-full max-w-md rounded-lg border bg-card p-4">
        <div className="space-y-2">
          <p className="text-sm font-medium">Find it here:</p>
          <div className="flex items-center gap-2 rounded-md bg-muted p-3">
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              <span className="font-semibold">KB Selector</span> in the left sidebar
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Look for &quot;Sample KB&quot; in the Knowledge Base dropdown menu
          </p>
        </div>
      </div>
    </div>
  );
}
