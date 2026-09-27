import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { login, register } from '../api/auth';
import { Code } from 'lucide-react';

export const Login = () => {
  const { loginToken } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, username, password);
      }
      const data = await login(email, password);
      loginToken(data.access_token);
    } catch (err: any) {
      let errorMsg = 'An error occurred';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errorMsg = detail;
        } else if (Array.isArray(detail)) {
          errorMsg = detail.map((d: any) => d.msg).join(', ');
        }
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-zinc-50 p-4">
      <div className="w-full max-w-sm bg-white p-8 rounded-2xl shadow-sm border border-zinc-100">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center mb-4">
            <Code className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-zinc-900">Skill Quest</h1>
          <p className="text-zinc-500 mt-2 text-sm">Every weekend, experience something new.</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 break-words">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type={isRegister ? "email" : "text"}
            placeholder={isRegister ? "Email Address" : "Email or Username"}
            className="w-full px-4 py-3 rounded-xl border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-zinc-50"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {isRegister && (
            <input
              type="text"
              placeholder="Username"
              className="w-full px-4 py-3 rounded-xl border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-zinc-50"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          )}
          <input
            type="password"
            placeholder="Password"
            className="w-full px-4 py-3 rounded-xl border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-zinc-50"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white font-medium py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 mt-2"
          >
            {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <button
          onClick={() => setIsRegister(!isRegister)}
          className="w-full text-center mt-6 text-sm text-zinc-500 hover:text-zinc-900"
        >
          {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
        </button>
      </div>
    </div>
  );
};
