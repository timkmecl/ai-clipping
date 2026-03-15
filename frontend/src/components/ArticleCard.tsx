import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, ExternalLink, Link as LinkIcon } from 'lucide-react';
import { Article } from '../types';

interface MediaGroupProps {
  medij: string;
  articles: Article[];
  mainTab: 'splosno' | 'nasprotniki' | 'podporniki';
  date: string;
}

export const MediaGroup: React.FC<MediaGroupProps> = ({ medij, articles, mainTab, date }) => {
  const navigate = useNavigate();

  const handleDownload = (id: string) => {
    const url = `${process.env.API_URL}/download/${date}/${id}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const shortenTag = (oz: string) => (oz === "ZAKON O POMOČI PRI PROSTOVOLJNEM KONČANJU ŽIVLJENJA") ? "ZPPKŽ" : oz;

  return (
    <div className="bg-white rounded-2xl border border-border overflow-hidden shadow-sm">
      <div className="bg-bg-secondary px-6 py-4 border-b border-border">
        <h4 className="text-lg font-serif">{medij}</h4>
      </div>
      <div className="divide-y divide-border">
        {articles.map(article => {
          const data = article.contents[mainTab];
          
          return (
            <div key={article.id} className="p-6 md:p-8">
              <div className="flex justify-between items-start mb-6 gap-4">
                <div className="text-xs text-text-secondary flex items-center gap-2 flex-wrap mt-1">
                  <span className="font-medium text-text-primary">{article.medij}</span>
                  <span>•</span>
                  <span>{article.datum}</span>
                  {article.avtor && (
                    <>
                      <span>•</span>
                      <span>{article.avtor}</span>
                    </>
                  )}
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button 
                    onClick={() => handleDownload(article.id)}
                    className="p-2 bg-bg-secondary hover:bg-border text-text-secondary rounded-lg transition-colors"
                    title="Prenesi PDF"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  {article.url && (
                    <a 
                      href={article.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="p-2 bg-bg-secondary hover:bg-border text-text-secondary rounded-lg transition-colors"
                      title="Odpri povezavo"
                    >
                      <LinkIcon className="w-4 h-4" />
                    </a>
                  )}
                  <button 
                    onClick={() => navigate(`/article/${article.id}`)}
                    className="p-2 bg-text-primary hover:bg-text-primary/90 text-white rounded-lg transition-colors"
                    title="Prikaži podrobnosti"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="flex flex-col md:flex-row gap-8">
                <div className="md:w-1/3 space-y-4">
                  <h5 className="text-xl font-serif leading-tight">{article.naslov}</h5>
                  <p className="text-sm text-text-secondary italic">"{article.intro}"</p>
                  <div className="flex flex-wrap gap-2">
                    {article.oznaka.map(oz => (
                      <span key={oz} className="text-xs px-2 py-1 bg-bg-secondary text-text-secondary rounded border border-border">#{shortenTag(oz)}</span>
                    ))}
                  </div>
                </div>
                
                <div className="md:w-2/3">
                  {data && (
                    <div className="space-y-6">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wider text-text-secondary mb-2">Povzetek</div>
                        <p className="text-text-primary">{data.povzetek}</p>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wider text-text-secondary mb-3">Poudarki</div>
                        <ul className="space-y-2">
                          {data.highlights.map((hl, i) => (
                            <li key={i} className="flex gap-3 text-sm text-text-secondary">
                              <span className="text-accent mt-0.5">•</span>
                              <span>{hl}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
