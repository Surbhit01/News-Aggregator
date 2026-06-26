import { useState, useEffect } from 'react';
import { getArticles, type ArticleSummary } from '../api/digest';
import ArticleCard from '../components/ArticleCard';

export default function Articles() {
  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxMinutes, setMaxMinutes] = useState<number | ''>('');
  const [sortBy, setSortBy] = useState<'relevance' | 'date'>('relevance');

  useEffect(() => {
    loadArticles();
  }, [maxMinutes, sortBy]);

  const loadArticles = async () => {
    setLoading(true);
    try {
      const params: any = { limit: 20 };
      if (maxMinutes) params.max_minutes = maxMinutes;
      const data = await getArticles(params);
      const sorted = [...data].sort((a, b) =>
        sortBy === 'relevance' ? b.relevance_score - a.relevance_score : new Date(b.published_at || 0).getTime() - new Date(a.published_at || 0).getTime()
      );
      setArticles(sorted);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Articles</h1>
        <div className="flex items-center gap-3">
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}
            className="input-field w-auto text-sm">
            <option value="relevance">Sort by Relevance</option>
            <option value="date">Sort by Date</option>
          </select>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-500">Max:</label>
            <input type="number" min={1} value={maxMinutes} placeholder="Any"
              onChange={(e) => setMaxMinutes(e.target.value ? Number(e.target.value) : '')}
              className="input-field w-20 text-sm" />
            <span className="text-sm text-gray-400">min</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">{[1, 2, 3].map((i) => <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />)}</div>
      ) : articles.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No articles found. Try adjusting your filters.</p>
      ) : (
        <div className="space-y-4">
          {articles.map((article) => <ArticleCard key={article.id} article={article} />)}
        </div>
      )}
    </div>
  );
}