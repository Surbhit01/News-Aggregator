export default function ReadingTimeBadge({ minutes }: { minutes: number | null }) {
  if (!minutes) return null;
  const icon = minutes <= 3 ? '⚡' : minutes <= 7 ? '📖' : '📚';
  return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-500" title="Estimated reading time">
      <span>{icon}</span>
      <span>{minutes} min</span>
    </span>
  );
}