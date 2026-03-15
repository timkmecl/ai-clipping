import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

const API_URL = process.env.API_URL;

interface User {
  name: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  error: string;
  login: (password: string) => Promise<boolean>;
  logout: () => void;
  setError: (error: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/verify`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setTimeout(() => {
            setIsAuthenticated(true);
            setUser({ name: 'Uporabnik' });
          }, 500);
        }
      })
      .finally(() => {setTimeout(() => setIsLoading(false), 500)});
  }, []);

  const login = useCallback(async (password: string) => {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
        credentials: 'include',
      });

      if (response.ok) {
        setIsAuthenticated(true);
        setUser({ name: 'Uporabnik' });
        setError('');
        return true;
      } else {
        setError('Napačno geslo');
        setUser(null);
        return false;
      }
    } catch (err) {
      setError('Prijava ni uspela');
      setUser(null);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    fetch(`${API_URL}/logout`, {
      method: 'POST',
      credentials: 'include',
    })
      .then(() => {
        setIsAuthenticated(false);
        setUser(null);
      })
      .catch(() => {
        setIsAuthenticated(false);
        setUser(null);
      });
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, error, isLoading, login, logout, setError }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};