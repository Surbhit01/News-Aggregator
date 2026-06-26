import { useState, useEffect } from 'react';
import { getPreferences, updatePreferences, getPreferenceStats, type UserPreferences, type PreferenceStats } from '../api/preferences';

const ALL_CATEGORIES = ['Technology', 'Finance', 'Geopolitics', 'Science', 'Health', 'Sports', 'Business', 'Entertainment'];

export default function Dashboard() {
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
  const [stats, setStats] = useState<PreferenceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [newKeyword, setNewKeyword] = useState('');
  const [newSource, setNewSource] = useState('');
  const [newBlocked, setNewBlocked] = useState('');
  const [newEntityType, setNewEntityType] = useState('stock');
  const [newEntityName, setNewEntityName] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    Promise.all([getPreferences(), getPreferenceStats()])
      .then(([p, s]) => { setPrefs(p); setStats(s); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const savePrefs = async (updated: Partial<UserPreferences>) => {
    if (!prefs) return;
    setSaving(true);
    try {
      const result = await updatePreferences({
        categories: updated.categories ?? prefs.categories,
        keywords: updated.keywords ?? prefs.keywords,
        preferred_sources: updated.preferred_sources ?? prefs.preferred_sources,
        blocked_sources: updated.blocked_sources ?? prefs.blocked_sources,
        tracked_entities: updated.tracked_entities ?? prefs.tracked_entities,
      });
      setPrefs(result);
      const s = await getPreferenceStats();
      setStats(s);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const toggleCategory = async (cat: string) => {
    if (!prefs) return;
    const categories = prefs.categories.includes(cat)
      ? prefs.categories.filter((c) => c !== cat)
      : [...prefs.categories, cat];
    await savePrefs({ categories });
  };

  const addKeyword = async () => {
    if (!prefs || !newKeyword.trim()) return;
    if (prefs.keywords.includes(newKeyword.trim())) { setNewKeyword(''); return; }
    await savePrefs({ keywords: [...prefs.keywords, newKeyword.trim()] });
    setNewKeyword('');
  };

  const removeKeyword = async (kw: string) => {
    if (!prefs) return;
    await savePrefs({ keywords: prefs.keywords.filter((k) => k !== kw) });
  };

  const addPreferredSource = async () => {
    if (!prefs || !newSource.trim()) return;
    const url = newSource.trim().startsWith('http') ? newSource.trim() : `https://${newSource.trim()}`;
    if (prefs.preferred_sources.includes(url)) { setNewSource(''); return; }
    await savePrefs({ preferred_sources: [...prefs.preferred_sources, url] });
    setNewSource('');
  };

  const removePreferredSource = async (src: string) => {
    if (!prefs) return;
    await savePrefs({ preferred_sources: prefs.preferred_sources.filter((s) => s !== src) });
  };

  const addBlockedSource = async () => {
    if (!prefs || !newBlocked.trim()) return;
    const url = newBlocked.trim().startsWith('http') ? newBlocked.trim() : `https://${newBlocked.trim()}`;
    if (prefs.blocked_sources.includes(url)) { setNewBlocked(''); return; }
    await savePrefs({ blocked_sources: [...prefs.blocked_sources, url] });
    setNewBlocked('');
  };

  const removeBlockedSource = async (src: string) => {
    if (!prefs) return;
    await savePrefs({ blocked_sources: prefs.blocked_sources.filter((s) => s !== src) });
  };

  const addTrackedEntity = async () => {
    if (!prefs || !newEntityName.trim()) return;
    const entity = { type: newEntityType, name: newEntityName.trim() };
    await savePrefs({ tracked_entities: [...prefs.tracked_entities, entity] });
    setNewEntityName('');
  };

  const removeTrackedEntity = async (idx: number) => {
    if (!prefs) return;
    await savePrefs({ tracked_entities: prefs.tracked_entities.filter((_, i) => i !== idx) });
  };

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full" /></div>;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Preferences</h1>
        {saved && <span className="text-sm text-green-600">Saved ✓</span>}
        {saving && <span className="text-sm text-gray-400">Saving...</span>}
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-5 gap-3 mb-8">
          {[
            { label: 'Categories', value: stats.total_categories },
            { label: 'Keywords', value: stats.total_keywords },
            { label: 'Preferred', value: stats.total_preferred_sources },
            { label: 'Blocked', value: stats.total_blocked_sources },
            { label: 'Tracked', value: stats.total_tracked_entities },
          ].map((s) => (
            <div key={s.label} className="card text-center py-3">
              <div className="text-2xl font-bold text-blue-600">{s.value}</div>
              <div className="text-xs text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Categories */}
      <section className="card mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">News Categories</h2>
        <div className="flex flex-wrap gap-2">
          {ALL_CATEGORIES.map((cat) => (
            <button key={cat} onClick={() => toggleCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                prefs?.categories.includes(cat)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}>
              {cat}
            </button>
          ))}
        </div>
      </section>

      {/* Keywords */}
      <section className="card mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Keywords & Topics</h2>
        <div className="flex gap-2 mb-3">
          <input type="text" className="input-field flex-1" placeholder="e.g., AI regulation"
            value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addKeyword()} />
          <button onClick={addKeyword} className="btn-primary">Add</button>
        </div>
        <div className="flex flex-wrap gap-2">
          {prefs?.keywords.map((kw) => (
            <span key={kw} className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm">
              {kw}
              <button onClick={() => removeKeyword(kw)} className="text-gray-400 hover:text-red-500 ml-1">✕</button>
            </span>
          ))}
          {(!prefs?.keywords || prefs.keywords.length === 0) && (
            <p className="text-sm text-gray-400">No keywords added yet</p>
          )}
        </div>
      </section>

      {/* Preferred Sources */}
      <section className="card mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Preferred Sources</h2>
        <p className="text-xs text-gray-500 mb-3">Articles from these sources will be prioritized</p>
        <div className="flex gap-2 mb-3">
          <input type="text" className="input-field flex-1" placeholder="e.g., reuters.com"
            value={newSource} onChange={(e) => setNewSource(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addPreferredSource()} />
          <button onClick={addPreferredSource} className="btn-primary">Add</button>
        </div>
        <div className="flex flex-wrap gap-2">
          {prefs?.preferred_sources.map((src) => (
            <span key={src} className="inline-flex items-center gap-1 px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm">
              {src.replace('https://', '')}
              <button onClick={() => removePreferredSource(src)} className="text-green-400 hover:text-red-500 ml-1">✕</button>
            </span>
          ))}
          {(!prefs?.preferred_sources || prefs.preferred_sources.length === 0) && (
            <p className="text-sm text-gray-400">No preferred sources set</p>
          )}
        </div>
      </section>

      {/* Blocked Sources */}
      <section className="card mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Blocked Sources</h2>
        <p className="text-xs text-gray-500 mb-3">Articles from these sources will be excluded</p>
        <div className="flex gap-2 mb-3">
          <input type="text" className="input-field flex-1" placeholder="e.g., breitbart.com"
            value={newBlocked} onChange={(e) => setNewBlocked(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addBlockedSource()} />
          <button onClick={addBlockedSource} className="btn-primary">Add</button>
        </div>
        <div className="flex flex-wrap gap-2">
          {prefs?.blocked_sources.map((src) => (
            <span key={src} className="inline-flex items-center gap-1 px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm">
              {src.replace('https://', '')}
              <button onClick={() => removeBlockedSource(src)} className="text-red-400 hover:text-red-700 ml-1">✕</button>
            </span>
          ))}
          {(!prefs?.blocked_sources || prefs.blocked_sources.length === 0) && (
            <p className="text-sm text-gray-400">No blocked sources set</p>
          )}
        </div>
      </section>

      {/* Tracked Entities */}
      <section className="card mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Tracked Entities</h2>
        <p className="text-xs text-gray-500 mb-3">News mentioning these will be boosted (stocks, industries, cities, etc.)</p>
        <div className="flex gap-2 mb-3">
          <select value={newEntityType} onChange={(e) => setNewEntityType(e.target.value)}
            className="input-field w-32 text-sm">
            <option value="stock">Stock</option>
            <option value="industry">Industry</option>
            <option value="city">City</option>
            <option value="company">Company</option>
            <option value="person">Person</option>
          </select>
          <input type="text" className="input-field flex-1" placeholder="e.g., AAPL, Tesla, London"
            value={newEntityName} onChange={(e) => setNewEntityName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addTrackedEntity()} />
          <button onClick={addTrackedEntity} className="btn-primary">Add</button>
        </div>
        <div className="flex flex-wrap gap-2">
          {prefs?.tracked_entities.map((entity, idx) => (
            <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm">
              [{entity.type}] {entity.name}
              <button onClick={() => removeTrackedEntity(idx)} className="text-purple-400 hover:text-red-500 ml-1">✕</button>
            </span>
          ))}
          {(!prefs?.tracked_entities || prefs.tracked_entities.length === 0) && (
            <p className="text-sm text-gray-400">No tracked entities set</p>
          )}
        </div>
      </section>

      {/* Implicit Preferences */}
      {prefs?.implicit_preferences && Object.keys(prefs.implicit_preferences).length > 0 && (
        <section className="card">
          <h2 className="font-semibold text-gray-800 mb-3">Learned Preferences</h2>
          <p className="text-xs text-gray-500 mb-3">Automatically learned from your reading behavior</p>
          <div className="space-y-2">
            {Object.entries(prefs.implicit_preferences).sort(([, a], [, b]) => b - a).slice(0, 10).map(([topic, score]) => (
              <div key={topic} className="flex items-center gap-3">
                <span className="text-sm text-gray-700 w-32 truncate">{topic}</span>
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${score * 100}%` }} />
                </div>
                <span className="text-xs text-gray-400 w-10 text-right">{Math.round(score * 100)}%</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}