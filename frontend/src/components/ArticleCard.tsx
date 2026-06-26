import { useState } from 'react';
import BiasIndicator from './BiasIndicator';
import ReadingTimeBadge from './ReadingTimeBadge';
import type { ArticleSummary } from '../api/digest';
import { submitFeedback } from '../api/feedback';
import { logReading } from '../api/history';

interface Props {
  article: ArticleSummary;
}

type FeedbackState = 'show_more' | 'show_less' | 'irrelevant' | null;

export default function ArticleCard({ article }: Props) {
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleFeedback = async (type: 'show_more' | 'show_less' | 'irrelevant') => {
    if (submitting || feedback) return; // Prevent double-submit
    setSubmitting(true);
    try {
      await submitFeedback(article.id, type);
      setFeedback(type);
    } catch {
      // Silently fail — feedback is non-critical
    } finally {
      setSubmitting(false);
    }
  };

  const handleCardClick = () => {
    // Fire-and-forget: log the read in background
    logReading(article.id, 30).catch(() => {});
  };

  const isIrrelevant = feedback === 'irrelevant';
  const isPositive = feedback === 'show_more';
  const isNegative = feedback === 'show_less';

  return (
    <div
      className={`card transition-all duration-300 ${isIrrelevant ? 'opacity-50' : ''}`}
      onClick={handleCardClick}
    >
      {/* ── Header: Title + Badges ─────────────────────── */}
      <div className="flex items-start justify-between gap-4 mb-2">
        <h3 className="text-lg font-semibold text-gray-900 leading-snug">
          <a
            href={article.source_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="hover:text-blue-600 transition-colors"
          >
            {article.title}
          </a>
        </h3>
        <div className="flex items-center gap-2 shrink-0">
          <BiasIndicator rating={article.bias_rating} />
          <ReadingTimeBadge minutes={article.estimated_read_time_minutes} />
        </div>
      </div>

      {/* ── TL;DR ──────────────────────────────────────── */}
      {article.tl_dr && (
        <p className="text-sm text-gray-600 mb-3 leading-relaxed">{article.tl_dr}</p>
      )}

      {/* ── Key Takeaways ──────────────────────────────── */}
      {article.key_takeaways && article.key_takeaways.length > 0 && (
        <ul className="text-sm text-gray-500 mb-3 space-y-1">
          {article.key_takeaways.slice(0, 3).map((t, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-gray-300">•</span>
              <span>{t}</span>
            </li>
          ))}
        </ul>
      )}

      {/* ── Footer: Source + Feedback ──────────────────── */}
      <div className="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-100">
        {/* Left: Source + Impact */}
        <div className="flex items-center gap-3">
          <a
            href={article.source_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="hover:text-blue-600 transition-colors"
          >
            {article.source_name || article.source_url.split('/')[2]}
          </a>
          {article.impact_radar && article.impact_radar.length > 0 && (
            <span title="Impact areas" className="text-yellow-600">
              ⚡ {article.impact_radar.slice(0, 2).join(', ')}
            </span>
          )}
        </div>

        {/* Right: Feedback buttons */}
        <div className="flex items-center gap-1">
          {isPositive && <span className="text-green-600 text-xs mr-1">Saved</span>}
          {isNegative && <span className="text-red-600 text-xs mr-1">Saved</span>}
          {isIrrelevant && <span className="text-gray-400 text-xs mr-1">Dismissed</span>}

          {!feedback && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); handleFeedback('show_more'); }}
                disabled={submitting}
                className="px-2 py-1 rounded hover:bg-green-50 text-green-600 transition-colors disabled:opacity-40"
                title="Show more like this"
              >👍</button>
              <button
                onClick={(e) => { e.stopPropagation(); handleFeedback('show_less'); }}
                disabled={submitting}
                className="px-2 py-1 rounded hover:bg-red-50 text-red-600 transition-colors disabled:opacity-40"
                title="Show less like this"
              >👎</button>
              <button
                onClick={(e) => { e.stopPropagation(); handleFeedback('irrelevant'); }}
                disabled={submitting}
                className="px-2 py-1 rounded hover:bg-gray-100 text-gray-400 transition-colors disabled:opacity-40"
                title="Mark as irrelevant"
              >✕</button>
            </>
          )}

          {/* Active state: show only the selected button with highlight */}
          {isPositive && (
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded font-medium">👍</span>
          )}
          {isNegative && (
            <span className="px-2 py-1 bg-red-100 text-red-700 rounded font-medium">👎</span>
          )}
          {isIrrelevant && (
            <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded">✕ Dismissed</span>
          )}
        </div>
      </div>
    </div>
  );
}