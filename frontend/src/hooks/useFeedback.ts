'use client';

import { useState } from 'react';

import type { FeedbackType } from '@/components/generation/feedback-modal';
import type { Alternative } from '@/components/generation/recovery-modal';

interface FeedbackResponse {
  alternatives: Alternative[];
}

export function useFeedback(draftId: string) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [alternatives, setAlternatives] = useState<Alternative[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (feedbackType: FeedbackType, comments?: string): Promise<boolean> => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/drafts/${draftId}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feedback_type: feedbackType,
          comments,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Feedback submission failed: ${response.statusText}`);
      }

      const data: FeedbackResponse = await response.json();
      setAlternatives(data.alternatives);

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Feedback submission failed';
      setError(errorMessage);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetAlternatives = () => {
    setAlternatives([]);
    setError(null);
  };

  return {
    handleSubmit,
    isSubmitting,
    alternatives,
    error,
    resetAlternatives,
  };
}
