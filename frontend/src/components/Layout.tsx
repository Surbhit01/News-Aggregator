import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-blue-600">NewsAggregator</Link>
          {user && (
            <div className="flex items-center gap-4">
              <nav className="flex gap-4 text-sm">
                <Link to="/" className="text-gray-600 hover:text-blue-600">Digest</Link>
                <Link to="/articles" className="text-gray-600 hover:text-blue-600">Articles</Link>
                <Link to="/dashboard" className="text-gray-600 hover:text-blue-600">Preferences</Link>
              </nav>
              <span className="text-sm text-gray-400">{user.email}</span>
              <button onClick={handleLogout} className="text-sm text-red-500 hover:text-red-700">Logout</button>
            </div>
          )}
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto px-4 py-6 w-full">{children}</main>
    </div>
  );
}