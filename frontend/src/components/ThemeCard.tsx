import React from 'react';
import { Link } from 'react-router-dom';
import { ThemeItem } from '../types';

interface ThemeCardProps {
  theme: ThemeItem;
}

export const ThemeCard: React.FC<ThemeCardProps> = ({ theme }) => {
  return (
    <div className="bg-white rounded-2xl p-6 md:p-8 border border-border shadow-sm">
      <div className="flex flex-col md:flex-row gap-8">
        <div className="md:w-1/3">
          <h4 className="text-2xl font-serif mb-4 leading-tight">{theme.naslov}</h4>
          <div className="flex flex-wrap gap-2 mb-4">
            {theme.mediji.map((m, i) => (
              <Link 
                key={m + i} 
                to={`/article/${theme.ids[i]}`}
                className="text-xs font-medium px-2.5 py-1 bg-bg-secondary text-text-secondary hover:text-text-primary hover:bg-border rounded-md border border-border transition-colors"
              >
                {m}
              </Link>
            ))}
          </div>
          <div className="text-sm text-text-secondary">
            Število člankov: {theme.ids.length}
          </div>
        </div>
        <div className="md:w-2/3 space-y-6">
          <div>
            <div className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-2">Povzetek</div>
            <p className="text-lg text-text-primary">{theme.povzetek}</p>
          </div>
          {theme.highlights.length > 0 && (
            <div>
              <div className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">Ključne točke</div>
              <ul className="space-y-3">
                {theme.highlights.map((hl, i) => (
                  <li key={i} className="flex gap-3 text-text-secondary">
                    <span className="text-accent mt-1">•</span>
                    <span>{hl}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
