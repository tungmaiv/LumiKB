/**
 * HighlightedText component for keyword highlighting in search results
 * Story 3.9: Relevance Explanation (AC2)
 *
 * Highlights keywords from a search query within text using <mark> elements.
 * - Case-insensitive matching
 * - Word boundary preservation (no partial highlights)
 * - Yellow background (#FFF4E6) with dark text
 */

interface HighlightedTextProps {
  text: string;
  keywords: string[];
}

export function HighlightedText({ text, keywords }: HighlightedTextProps) {
  // Early return if no keywords to highlight
  if (!keywords || keywords.length === 0) {
    return <span>{text}</span>;
  }

  // Build regex from keywords (case-insensitive, word boundaries)
  const escaped = keywords
    .map((kw) => kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) // Escape regex special chars
    .join('|');
  const regex = new RegExp(`\\b(${escaped})\\b`, 'gi');

  // Split text into parts (highlighted vs plain)
  const parts: { text: string; highlight: boolean }[] = [];
  let lastIndex = 0;

  // Use replace to find matches, but don't actually replace
  text.replace(regex, (match, _, offset) => {
    // Add plain text before match
    if (offset > lastIndex) {
      parts.push({ text: text.slice(lastIndex, offset), highlight: false });
    }
    // Add highlighted match
    parts.push({ text: match, highlight: true });
    lastIndex = offset + match.length;
    return match;
  });

  // Add remaining plain text
  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex), highlight: false });
  }

  return (
    <>
      {parts.map((part, i) =>
        part.highlight ? (
          <mark key={i} className="bg-yellow-100 dark:bg-yellow-900/30 rounded px-0.5">
            {part.text}
          </mark>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
    </>
  );
}
