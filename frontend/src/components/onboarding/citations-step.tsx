import { FileText, CheckCircle2 } from 'lucide-react';

export function CitationsStep() {
  return (
    <div className="flex flex-col items-center space-y-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/20">
        <FileText className="h-8 w-8 text-purple-600 dark:text-purple-400" />
      </div>

      <div className="space-y-3 text-center">
        <h2 className="text-2xl font-bold">Citations Build Trust</h2>
        <p className="text-muted-foreground max-w-md">
          Every answer shows its sources. Click any citation number to see the exact document
          passage.
        </p>
      </div>

      <div className="w-full max-w-md space-y-4">
        <div className="rounded-lg border bg-card p-4">
          <div className="space-y-3">
            <p className="text-sm">
              LumiKB provides semantic search with citations{' '}
              <sup className="text-xs text-primary font-medium">[1]</sup>. All answers are traceable
              to source documents <sup className="text-xs text-primary font-medium">[2]</sup>.
            </p>

            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-500" />
                <span>Citation numbers link to exact passages</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-500" />
                <span>Citation sidebar shows source context</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-3 w-3 flex-shrink-0 text-green-500" />
                <span>Verify any answer in one click</span>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-muted p-3 text-center">
          <p className="text-sm font-medium">Trust through verifiability</p>
        </div>
      </div>
    </div>
  );
}
