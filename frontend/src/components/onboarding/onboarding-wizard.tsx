'use client';

import { useState } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { WelcomeStep } from './welcome-step';
import { ExploreKBStep } from './explore-kb-step';
import { TrySearchStep } from './try-search-step';
import { CitationsStep } from './citations-step';
import { CompletionStep } from './completion-step';

interface OnboardingWizardProps {
  onComplete: () => void;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [showSkipConfirmation, setShowSkipConfirmation] = useState(false);
  const totalSteps = 5;

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    setShowSkipConfirmation(true);
  };

  const handleConfirmSkip = () => {
    onComplete();
  };

  const handleCancelSkip = () => {
    setShowSkipConfirmation(false);
  };

  // Render current step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <WelcomeStep />;
      case 2:
        return <ExploreKBStep />;
      case 3:
        return <TrySearchStep />;
      case 4:
        return <CitationsStep />;
      case 5:
        return <CompletionStep />;
      default:
        return <WelcomeStep />;
    }
  };

  return (
    <>
      {/* Main wizard dialog */}
      <Dialog open={!showSkipConfirmation} modal>
        <DialogContent
          className="max-w-2xl"
          onEscapeKeyDown={(e) => {
            e.preventDefault();
            handleSkip();
          }}
          onPointerDownOutside={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
        >
          <div className="space-y-6">
            {/* Progress dots */}
            <div className="flex justify-center gap-2">
              {Array.from({ length: totalSteps }).map((_, index) => (
                <div
                  key={index}
                  className={`h-2 w-2 rounded-full ${
                    index + 1 === currentStep
                      ? 'bg-primary'
                      : index + 1 < currentStep
                        ? 'bg-primary/50'
                        : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>

            {/* Step counter */}
            <div className="text-center text-sm text-muted-foreground">
              Step {currentStep} of {totalSteps}
            </div>

            {/* Step content */}
            <div className="min-h-[300px]">{renderStepContent()}</div>

            {/* Navigation controls */}
            <div className="flex items-center justify-between">
              <Button variant="ghost" onClick={handleBack} disabled={currentStep === 1}>
                Back
              </Button>

              <button
                onClick={handleSkip}
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                Skip Tutorial
              </button>

              {currentStep < totalSteps ? (
                <Button onClick={handleNext}>Next</Button>
              ) : (
                <Button onClick={onComplete}>Start Exploring</Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Skip confirmation dialog */}
      <Dialog open={showSkipConfirmation} onOpenChange={setShowSkipConfirmation}>
        <DialogContent className="max-w-md">
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Skip Tutorial?</h2>
            <p className="text-sm text-muted-foreground">
              Are you sure you want to skip the tutorial? You can restart it later from Settings.
            </p>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={handleCancelSkip}>
                Cancel
              </Button>
              <Button onClick={handleConfirmSkip}>Skip</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
