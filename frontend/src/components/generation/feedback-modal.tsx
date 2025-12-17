'use client';

import { AlertTriangle } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';

export type FeedbackType =
  | 'not_relevant'
  | 'wrong_format'
  | 'needs_more_detail'
  | 'low_confidence'
  | 'other';

interface FeedbackOption {
  value: FeedbackType;
  label: string;
  description: string;
}

const FEEDBACK_OPTIONS: FeedbackOption[] = [
  {
    value: 'not_relevant',
    label: 'Results aren&apos;t relevant',
    description: 'Draft doesn&apos;t address my context',
  },
  {
    value: 'wrong_format',
    label: 'Wrong format or structure',
    description: 'I need a different template',
  },
  {
    value: 'needs_more_detail',
    label: 'Needs more detail',
    description: 'Too high-level, missing specifics',
  },
  {
    value: 'low_confidence',
    label: 'Low confidence sources',
    description: 'Citations seem weak or off-topic',
  },
  {
    value: 'other',
    label: 'Other issue',
    description: 'Describe what went wrong',
  },
];

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (feedbackType: FeedbackType, comments?: string) => void;
  isSubmitting?: boolean;
}

export function FeedbackModal({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
}: FeedbackModalProps) {
  const [selectedType, setSelectedType] = useState<FeedbackType | null>(null);
  const [comments, setComments] = useState('');

  const handleSubmit = () => {
    if (!selectedType) return;

    onSubmit(selectedType, comments || undefined);

    // Reset form
    setSelectedType(null);
    setComments('');
  };

  const handleClose = () => {
    // Reset form on close
    setSelectedType(null);
    setComments('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            What went wrong?
          </DialogTitle>
          <DialogDescription>
            Help us improve by telling us what didn&apos;t work with this draft.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <RadioGroup
            value={selectedType || undefined}
            onValueChange={(value) => setSelectedType(value as FeedbackType)}
          >
            {FEEDBACK_OPTIONS.map((option) => (
              <div key={option.value} className="flex items-start space-x-3">
                <RadioGroupItem value={option.value} id={option.value} className="mt-1" />
                <div className="grid gap-1">
                  <Label htmlFor={option.value} className="cursor-pointer font-medium">
                    {option.label}
                  </Label>
                  <p className="text-sm text-muted-foreground">{option.description}</p>
                </div>
              </div>
            ))}
          </RadioGroup>

          {selectedType === 'other' && (
            <div className="space-y-2 pt-2">
              <Label htmlFor="comments">Comments</Label>
              <Textarea
                id="comments"
                placeholder="Describe what went wrong..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                maxLength={500}
                rows={4}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground text-right">
                {comments.length}/500 characters
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!selectedType || isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
