import { useState } from 'react';
import { Lock, User, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

export default function Login({ onLogin, API_BASE_URL }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        onLogin(data.access_token, data.user);
      } else {
        setError(data.detail || 'Invalid username or password');
      }
    } catch (err) {
      console.error("Login error:", err);
      setError('Connection failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in duration-300">
        
        {/* Header */}
        <div className="bg-emerald-800 p-8 text-center text-white">
          <div className="mx-auto w-16 h-16 bg-emerald-700 rounded-2xl flex items-center justify-center mb-4 shadow-lg ring-4 ring-emerald-600/30">
            <ShieldCheck className="w-10 h-10 text-emerald-300" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Syngenta Co-Pilot</h1>
          <p className="text-emerald-200/80 text-sm mt-1">Secure Field Operations Portal</p>
        </div>

        {/* Form */}
        <div className="p-8 space-y-6">
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl flex items-start space-x-3 animate-in slide-in-from-top-2">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5 block">
                Username
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 pl-11 pr-4 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all shadow-inner"
                  placeholder="e.g. rep1"
                />
                <User className="absolute left-3.5 top-3.5 w-5 h-5 text-slate-400" />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5 block">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 pl-11 pr-4 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all shadow-inner"
                  placeholder="••••••••"
                />
                <Lock className="absolute left-3.5 top-3.5 w-5 h-5 text-slate-400" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2 active:scale-[0.98] disabled:opacity-70"
            >
              {loading ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  <span>Secure Sign In</span>
                </>
              )}
            </button>
          </form>

          <div className="pt-4 text-center border-t border-slate-100">
            <p className="text-xs text-slate-400 leading-relaxed italic">
              Access is restricted to authorized Syngenta Field Representatives. 
              Contact territory admin for credentials.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
