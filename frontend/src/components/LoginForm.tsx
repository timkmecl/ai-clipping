import React, { useState } from 'react';
import { Lock } from 'lucide-react';
import { motion } from 'motion/react';

interface LoginFormProps {
  onLogin: (password: string) => boolean;
  error: string;
}

export function LoginForm({ onLogin, error }: LoginFormProps) {
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin(password);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-primary p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white p-8 rounded-2xl shadow-sm border border-border max-w-md w-full"
      >
        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-bg-secondary rounded-full flex items-center justify-center">
            <Lock className="w-6 h-6 text-text-secondary" />
          </div>
        </div>
        <h1 className="text-4xl font-serif text-center mb-2">AI Media Clipping</h1>
        <p className="text-text-secondary text-center mb-8">Vnesite geslo za dostop do analize</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Geslo"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all"
            />
            {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
          </div>
          <button
            type="submit"
            className="w-full bg-text-primary text-white py-3 rounded-xl font-medium hover:bg-text-primary/90 transition-colors"
          >
            Vstopi
          </button>
        </form>
      </motion.div>
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center text-xs text-gray-400 font-light mt-8 tracking-widest uppercase"
      >
        Built by{' '}
        <a href="https://kmecl.eu" target="_blank" rel="noopener noreferrer" className="underline hover:text-[#BC5A41]">Tim Kmecl</a> 2026
      </motion.div>
    </div>
  );
}
