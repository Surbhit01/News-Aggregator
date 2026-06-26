import { useState, useEffect, useRef } from 'react';
import { getDigest, type DigestResponse } from '../api/digest';
import ArticleCard from '../components/ArticleCard';

const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 15; // ~45 seconds max wait

export default function Digest() {
  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const pollCount = useRef(0);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadDigest = async () => {
    setLoading(true);
    setMessage('');
    try {
      const data = await getDigest('daily');
      setDigest(data);
      pollCount.current = 0; // Reset on success
    } catch (err: any) {
      if (err.response?.status === 202) {
        setMessage(err.response.data.detail || 'Digest is being generated...');
        // Auto-poll if under max attempts
        if (pollCount.current < MAX_POLL_ATTEMPTS) {
          pollCount.current += 1;
          pollTimer.current = setTimeout(loadDigest, POLL_INTERVAL_MS);
        } else {
          setMessage('Digest generation is taking longer than expected. Click Retry to try again.');
        }
      } else {
        setMessage('Could not load digest. Check back later.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDigest();
    return () => {
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full mb-4" />
        <p className="text-gray-500">Loading your digest...</p>
      </div>
    );
  }

  if (message) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-gray-600 mb-4">{message}</p>
        <button onClick={loadDigest} className="btn-primary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {digest?.title || 'Morning Briefing'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {digest?.generated_at
              ? new Date(digest.generated_at).toLocaleDateString('en-US', {
                  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                })
              : ''}
          </p>
        </div>
        <button onClick={loadDigest} className="btn-secondary text-sm">
          Refresh
        </button>
      </div>


      {/* Articles shown as styled cards — raw content hidden to avoid duplication */}
      {digest?.articles && digest.articles.length > 0 ? (
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Articles ({digest.articles.length})
          </h2>
          <div className="space-y-4">
            {digest.articles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
        </div>
      ) : (
        <p className="text-gray-500 text-center py-8">No articles in this digest yet.</p>
      )}
    </div>
  );
}