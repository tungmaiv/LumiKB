/**
 * Provider Logo Component
 * Story 7-9: LLM Model Registry
 *
 * Renders SVG logos for LLM providers
 */

import type { ReactElement } from 'react';

import type { ModelProvider } from '@/types/llm-model';

interface ProviderLogoProps {
  provider: ModelProvider;
  size?: number;
  className?: string;
}

export function ProviderLogo({ provider, size = 20, className = '' }: ProviderLogoProps) {
  const logos: Record<ModelProvider, ReactElement> = {
    openai: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364l2.0201-1.1638a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6099-1.4997Z" />
      </svg>
    ),
    anthropic: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M17.3041 3.541h-3.6718l6.696 16.918h3.6718L17.3041 3.541zm-10.6082 0L0 20.459h3.7965l1.3589-3.5095h6.7893l1.3638 3.5095h3.7965L10.4123 3.541H6.696zm.8532 10.1592 2.2386-5.7733 2.2386 5.7733H7.5492z" />
      </svg>
    ),
    azure: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M13.05 4.24L6.56 18.05 2 18l11.05-13.76zM14.47 4.65l-1.8 5.53 3.87 4.61-7.04 1.48h12.5l-7.53-11.62z" />
      </svg>
    ),
    gemini: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M12 0C5.37258 0 0 5.37258 0 12C0 18.6274 5.37258 24 12 24C18.6274 24 24 18.6274 24 12C24 5.37258 18.6274 0 12 0ZM18.2727 12C18.2727 15.4636 15.4636 18.2727 12 18.2727C8.53636 18.2727 5.72727 15.4636 5.72727 12C5.72727 8.53636 8.53636 5.72727 12 5.72727C15.4636 5.72727 18.2727 8.53636 18.2727 12Z" />
      </svg>
    ),
    cohere: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M8.545 12.198c0 1.639-.523 2.976-1.678 3.976-.933.824-2.124 1.28-3.54 1.28-.367 0-.743-.037-1.114-.102-.39-.07-.79-.183-1.188-.328-.122-.05-.188-.17-.188-.305V14.47c0-.193.188-.326.372-.26.502.184.948.288 1.328.288 1.305 0 1.98-.826 1.98-2.42V4.37c0-.204.166-.37.37-.37h3.288c.204 0 .37.166.37.37v7.829zm6.454.296c-1.138 0-2.06-.922-2.06-2.06s.922-2.06 2.06-2.06 2.06.922 2.06 2.06-.922 2.06-2.06 2.06zm9.001 4.225c0 .204-.166.37-.37.37h-3.287c-.205 0-.37-.166-.37-.37V4.369c0-.204.165-.37.37-.37h3.287c.204 0 .37.166.37.37v12.35z" />
      </svg>
    ),
    ollama: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-2-9c.83 0 1.5-.67 1.5-1.5S10.83 8 10 8s-1.5.67-1.5 1.5S9.17 11 10 11zm4 0c.83 0 1.5-.67 1.5-1.5S14.83 8 14 8s-1.5.67-1.5 1.5.67 1.5 1.5 1.5zm-2 5.5c2.14 0 3.92-1.5 4.38-3.5H7.62c.46 2 2.24 3.5 4.38 3.5z" />
      </svg>
    ),
    deepseek: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path
          d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
          strokeWidth="2"
          stroke="currentColor"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
    qwen: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h-2v-2h2v2zm0-4h-2V7h2v6zm4 4h-2v-6h2v6zm0-8h-2V7h2v2z" />
      </svg>
    ),
    mistral: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <rect x="1" y="3" width="5" height="5" />
        <rect x="18" y="3" width="5" height="5" />
        <rect x="1" y="9.5" width="5" height="5" />
        <rect x="6" y="9.5" width="5" height="5" fill="currentColor" fillOpacity="0.5" />
        <rect x="13" y="9.5" width="5" height="5" fill="currentColor" fillOpacity="0.5" />
        <rect x="18" y="9.5" width="5" height="5" />
        <rect x="1" y="16" width="5" height="5" />
        <rect x="6" y="16" width="5" height="5" />
        <rect x="13" y="16" width="5" height="5" />
        <rect x="18" y="16" width="5" height="5" />
      </svg>
    ),
    lmstudio: (
      <svg viewBox="0 0 24 24" width={size} height={size} className={className} fill="currentColor">
        <path d="M4 4h16v16H4V4zm2 2v12h12V6H6zm2 2h8v2H8V8zm0 4h8v2H8v-2zm0 4h5v2H8v-2z" />
      </svg>
    ),
  };

  return logos[provider] || null;
}

// Provider colors for styling
export const PROVIDER_COLORS: Record<ModelProvider, string> = {
  openai: 'text-[#10a37f]',
  anthropic: 'text-[#d97706]',
  azure: 'text-[#0078d4]',
  gemini: 'text-[#4285f4]',
  cohere: 'text-[#39594d]',
  ollama: 'text-gray-700 dark:text-gray-300',
  deepseek: 'text-[#5865f2]',
  qwen: 'text-[#ff6a00]',
  mistral: 'text-[#f54e42]',
  lmstudio: 'text-[#7c3aed]',
};
