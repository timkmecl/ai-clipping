import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Dashboard } from './features/Dashboard';
import { ArticleDetails } from './features/ArticleDetails';
import { LoginForm } from './components/LoginForm';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ClippingProvider } from './context/ClippingContext';

function AppContent() {
  const { isAuthenticated, error, login } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm onLogin={login} error={error} />;
  }

  return (
    <ClippingProvider>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/article/:date/:id" element={<ArticleDetails />} />
      </Routes>
    </ClippingProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
