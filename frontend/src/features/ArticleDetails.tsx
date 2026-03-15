import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Newspaper, ExternalLink as LinkIcon } from 'lucide-react';
import { motion } from 'motion/react';
import { Article } from '../types';
import { useClipping } from '../context/ClippingContext';

export const ArticleDetails: React.FC = () => {
  const { id, date } = useParams<{ id: string, date: string }>();
  const navigate = useNavigate();
  const { data, loading, loadData } = useClipping();

  useEffect(() => {
    if (!data) {
      loadData(date);
    }
  }, [data, loadData]);
  
  
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const article = data?.articles.find(a => a.id === id);

  const handleDownload = () => {
    const url = `${process.env.API_URL}/download/${data.date}/${article.id}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-primary">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-text-primary border-t-transparent rounded-full animate-spin"></div>
          <div className="text-text-secondary font-medium">Nalaganje podatkov...</div>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center p-6">
        <h2 className="text-2xl font-serif mb-4">Članek ni bil najden</h2>
        <button 
          onClick={() => navigate('/')}
          className="flex items-center gap-2 px-4 py-2 bg-text-primary text-white rounded-lg"
        >
          <ArrowLeft className="w-4 h-4" />
          Nazaj na pregled
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary pb-24">
      <header className="border-b border-border bg-white/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-4 flex justify-between items-center">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Nazaj
          </button>
          <div className="text-sm text-text-secondary font-medium">Podrobnosti članka</div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <motion.article 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl p-8 md:p-12 shadow-sm border border-border space-y-12"
        >
          {/* Header Info */}
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start gap-6 md:gap-4">
              <div className="order-2 md:order-1 flex-1 min-w-0">
                <div className="text-sm text-text-secondary mb-3 flex items-center gap-2 flex-wrap">
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
                <h1 className="text-4xl md:text-5xl font-serif leading-tight break-words">{article.naslov}</h1>
              </div>
              <div className="order-1 md:order-2 flex gap-2 flex-shrink-0 self-end md:self-start">
                <button 
                  onClick={handleDownload}
                  className="p-3 bg-bg-secondary hover:bg-border text-text-secondary rounded-xl transition-colors cursor-pointer"
                  title="Prenesi PDF"
                >
                  <Newspaper className="w-5 h-5" />
                </button>
                {article.url && (
                  <a 
                    href={article.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="p-3 bg-bg-secondary hover:bg-border text-text-secondary rounded-xl transition-colors cursor-pointer"
                    title="Odpri povezavo"
                  >
                    <LinkIcon className="w-5 h-5" />
                  </a>
                )}
                {/* <button 
                  disabled
                  className="p-3 bg-text-primary/50 text-white rounded-xl cursor-default"
                  title="Prikaži podrobnosti (Trenutni pogled)"
                >
                  <ExternalLink className="w-5 h-5" />
                </button> */}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {article.oznaka.map(oz => (
                <span key={oz} className="text-sm px-3 py-1 bg-bg-secondary text-text-secondary rounded-md border border-border">
                  #{oz}
                </span>
              ))}
            </div>
            
            <div className="p-6 bg-bg-secondary rounded-2xl border border-border">
              <p className="text-lg text-text-secondary italic">"{article.intro}"</p>
            </div>
          </div>

          {/* Splosno Section */}
          <div className="space-y-6 pt-8 border-t border-border">
            <h2 className="text-2xl font-serif">Splošni povzetek</h2>
            <div className="space-y-6">
              <p className="text-lg text-text-primary leading-relaxed">{article.contents.splosno.povzetek}</p>
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-4">Ključne točke</h3>
                <ul className="space-y-3">
                  {article.contents.splosno.highlights.map((hl, i) => (
                    <li key={i} className="flex gap-4 text-text-secondary">
                      <span className="text-accent mt-1">•</span>
                      <span>{hl}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Nasprotniki Section */}
          {article.contents.nasprotniki && (
            <div className="space-y-6 pt-8 border-t border-border">
              <h2 className="text-2xl font-serif">Nasprotniki</h2>
              <div className="space-y-6">
                <p className="text-lg text-text-primary leading-relaxed">{article.contents.nasprotniki.povzetek}</p>
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-4">Ključne točke</h3>
                  <ul className="space-y-3">
                    {article.contents.nasprotniki.highlights.map((hl, i) => (
                      <li key={i} className="flex gap-4 text-text-secondary">
                        <span className="text-accent mt-1">•</span>
                        <span>{hl}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Podporniki Section */}
          {article.contents.podporniki && (
            <div className="space-y-6 pt-8 border-t border-border">
              <h2 className="text-2xl font-serif">Podporniki</h2>
              <div className="space-y-6">
                <p className="text-lg text-text-primary leading-relaxed">{article.contents.podporniki.povzetek}</p>
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-4">Ključne točke</h3>
                  <ul className="space-y-3">
                    {article.contents.podporniki.highlights.map((hl, i) => (
                      <li key={i} className="flex gap-4 text-text-secondary">
                        <span className="text-accent mt-1">•</span>
                        <span>{hl}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </motion.article>
        <p className="text-center text-xs text-gray-400 font-light mt-8 tracking-widest uppercase">
          Built by{' '}
          <a href="https://kmecl.eu" target="_blank" rel="noopener noreferrer" className="underline hover:text-[#BC5A41]">Tim Kmecl</a> 2026
        </p>
      </main>
    </div>
  );
};
