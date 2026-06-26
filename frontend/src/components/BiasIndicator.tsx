const BIAS_COLORS: Record<string, string> = {
  liberal: 'bg-blue-100 text-blue-800',
  conservative: 'bg-red-100 text-red-800',
  neutral: 'bg-green-100 text-green-800',
  unknown: 'bg-gray-100 text-gray-500',
};

export default function BiasIndicator({ rating }: { rating: string | null }) {
  const color = BIAS_COLORS[rating?.toLowerCase() || 'unknown'] || BIAS_COLORS.unknown;
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {rating || 'Unknown'}
    </span>
  );
}