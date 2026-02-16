const SUGGESTIONS = [
  "Portfolio overview",
  "Run full analysis",
  "Recent decisions",
  "Market update",
];

interface SuggestionChipsProps {
  onSelect: (text: string) => void;
}

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {SUGGESTIONS.map((text) => (
        <button
          key={text}
          onClick={() => onSelect(text)}
          className="px-3 py-1.5 rounded-full border border-gray-300 text-sm text-gray-700 hover:bg-gray-100 hover:border-gray-400 transition-colors"
        >
          {text}
        </button>
      ))}
    </div>
  );
}
