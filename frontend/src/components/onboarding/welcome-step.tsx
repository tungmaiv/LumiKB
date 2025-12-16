import { Sparkles } from "lucide-react";

export function WelcomeStep() {
  return (
    <div className="flex flex-col items-center justify-center space-y-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
        <Sparkles className="h-10 w-10 text-primary" />
      </div>

      <div className="space-y-3">
        <h1 className="text-3xl font-bold">Welcome to LumiKB!</h1>
        <p className="text-lg text-muted-foreground">
          Your AI-powered knowledge management platform
        </p>
      </div>

      <div className="max-w-md space-y-2 rounded-lg bg-muted p-6">
        <p className="text-sm leading-relaxed">
          Transform how you access, synthesize, and create knowledge artifacts.
        </p>
        <p className="text-sm font-medium">
          Knowledge that never walks out the door.
        </p>
      </div>
    </div>
  );
}
