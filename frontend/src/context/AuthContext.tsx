import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, getCurrentUser } from '../api/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  loginToken: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const u = await getCurrentUser();
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('skillquest_token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }

    const handleUnauthorized = () => {
      setUser(null);
    };
    window.addEventListener('unauthorized', handleUnauthorized);
    return () => window.removeEventListener('unauthorized', handleUnauthorized);
  }, []);

  const loginToken = (token: string) => {
    localStorage.setItem('skillquest_token', token);
    fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('skillquest_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
