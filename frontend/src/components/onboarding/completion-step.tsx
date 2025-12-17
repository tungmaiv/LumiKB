import { Rocket, Upload, Search, FileEdit } from 'lucide-react';

export function CompletionStep() {
  return (
    <div className="flex flex-col items-center space-y-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
        <Rocket className="h-8 w-8 text-green-600 dark:text-green-400" />
      </div>

      <div className="space-y-3 text-center">
        <h2 className="text-2xl font-bold">You&apos;re All Set!</h2>
        <p className="text-muted-foreground max-w-md">
          Start exploring the Sample KB, or create your own Knowledge Base and upload documents.
        </p>
      </div>

      <div className="w-full max-w-md space-y-3">
        <p className="text-sm font-medium">Next steps:</p>
        <div className="space-y-2">
          <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
            <Upload className="h-5 w-5 text-blue-500" />
            <span className="text-sm">Upload your first document</span>
          </div>
          <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
            <Search className="h-5 w-5 text-green-500" />
            <span className="text-sm">Try asking questions</span>
          </div>
          <div className="flex items-center gap-3 rounded-lg border bg-card p-3">
            <FileEdit className="h-5 w-5 text-purple-500" />
            <span className="text-sm">Generate a draft document</span>
          </div>
        </div>
      </div>

      <div className="rounded-lg bg-primary/10 p-4 text-center">
        <p className="text-sm text-primary font-medium">
          Ready to explore? Click &quot;Start Exploring&quot; below!
        </p>
      </div>
    </div>
  );
}
