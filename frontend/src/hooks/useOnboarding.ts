import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useUser, useAuthStore } from '@/lib/stores/auth-store';
import { apiClient } from '@/lib/api/client';
import type { UserRead } from '@/types/user';

export function useOnboarding() {
  const queryClient = useQueryClient();
  const user = useUser();
  const setUser = useAuthStore((state) => state.setUser);

  const isOnboardingComplete = user?.onboarding_completed ?? true;

  const markOnboardingCompleteMutation = useMutation({
    mutationFn: async () => {
      return apiClient<UserRead>('/api/v1/users/me/onboarding', {
        method: 'PUT',
      });
    },
    onSuccess: (updatedUser) => {
      // Update the user in auth store directly
      setUser(updatedUser);
      // Also invalidate any user queries
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });

  return {
    isOnboardingComplete,
    markOnboardingComplete: markOnboardingCompleteMutation.mutateAsync,
    isLoading: markOnboardingCompleteMutation.isPending,
    error: markOnboardingCompleteMutation.error,
  };
}
