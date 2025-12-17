import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

export function TrySearchStep() {
  return (
    <div className="flex flex-col items-center space-y-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
        <Search className="h-8 w-8 text-green-600 dark:text-green-400" />
      </div>

      <div className="space-y-3 text-center">
        <h2 className="text-2xl font-bold">Ask Your First Question</h2>
        <p className="text-muted-foreground max-w-md">
          Search works with natural language. Try asking about anything in the Sample KB!
        </p>
      </div>

      <div className="w-full max-w-md space-y-4">
        <div className="rounded-lg border bg-card p-4">
          <p className="mb-2 text-sm font-medium">Try this example query:</p>
          <div className="relative">
            <Input value="What are the key features of LumiKB?" readOnly className="pr-10" />
            <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>

        <div className="rounded-lg bg-muted p-3 text-center">
          <p className="text-xs text-muted-foreground">
            💡 After completing this tutorial, you can try searching in the Search page or Chat page
          </p>
        </div>
      </div>
    </div>
  );
}
