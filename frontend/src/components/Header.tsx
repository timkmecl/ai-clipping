import React from 'react';
import { LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  currentDate: string;
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ currentDate, title = "AI Media Clipping" }) => {
  const { logout, user } = useAuth();

  return (
    <header className="border-b border-border bg-white/50 backdrop-blur-md sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex flex-col">
          <h1 className="text-2xl font-serif">{title}</h1>
          {false && <span className="text-[10px] uppercase tracking-widest text-gray-400 font-mono">Prijavljen: {user.name}</span>}
        </div>
        <div className="flex items-center gap-6">
          <div className="text-sm text-text-secondary font-medium">{currentDate}</div>
          <button 
            onClick={logout}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-black"
            title="Odjava"
          >
            <LogOut size={20} />
          </button>
        </div>
      </div>
    </header>
  );
};
