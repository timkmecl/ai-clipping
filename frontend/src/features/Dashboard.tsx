import React, { useEffect } from 'react';
import { LayoutGrid, List, Newspaper } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Article } from '../types';
import { isAggregator } from '../utils/helpers';
import { useTabPersistence } from '../hooks/useTabPersistence';
import { Header } from '../components/Header';
import { SummarySection } from '../components/SummarySection';
import { ThemeCard } from '../components/ThemeCard';
import { MediaGroup } from '../components/ArticleCard';
import { useClipping } from '../context/ClippingContext';

interface DashboardProps {}

export const Dashboard: React.FC<DashboardProps> = () => {
  const { mainTab, setMainTab, subTab, setSubTab } = useTabPersistence();
  const { data, loading, loadData } = useClipping();

  useEffect(() => {
    if (!data) {
      loadData();
    }
  }, [data, loadData]);

  const handlePrevDay = () => {
    if (data?.prevDate) {
      loadData(data.prevDate);
    }
  };

  const handleNextDay = () => {
    if (data?.nextDate) {
      loadData(data.nextDate);
    }
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

  if (!data) return null;

  // Filter articles based on whether they have data for the selected mainTab
  const relevantArticles = data.articles.filter(article => article.contents && article.contents[mainTab] !== null && article.contents[mainTab] !== undefined);

  // // Group relevant articles by media
  // const articlesByMedia = relevantArticles.reduce((acc, article) => {
  //   if (!acc[article.medij]) {
  //     acc[article.medij] = [];
  //   }
  //   acc[article.medij].push(article);
  //   return acc;
  // }, {} as Record<string, Article[]>);

  const mediaPriority = [
    'rtv',           // RTV SLO, rtvslo.si, TV Slovenija
    'mmc',
    '24ur',          // 24ur.com, POP TV
    'delo',          // Delo, Delo.si, Gostujoče pero
    'dnevnik',
    'n1',            // N1info.si, N1 Slovenija
    'večer',         
    'vecer',         // Večer, vecer.com
    'siol',          // Siol.net
    'slovenske novice', 
    'zurnal24',
    'žurnal24',
    'zurnal',        // Zurnal24.si
    'sta',           // Slovenska tiskovna agencija
    'finance',       // Finance.si
    'mladina',       // Mladina.si
    'reporter',      
    'domovina',
    'demokracija',
    'družina',
    'druzina',
    'nova24',
    'primorske',     // Primorske novice
  ];

  const getMediaRank = (mediaName: string): number => {
    const name = mediaName.toLowerCase();
    const index = mediaPriority.findIndex(keyword => name.includes(keyword));
    return index === -1 ? 999 : index;
  };

  let articlesByMedia = relevantArticles.reduce((acc, article) => {
    if (!acc[article.medij]) {
      acc[article.medij] = [];
    }
    acc[article.medij].push(article);
    return acc;
  }, {} as Record<string, Article[]>);

  const sortedMediaNames = Object.keys(articlesByMedia).sort((a, b) => {
    const rankA = getMediaRank(a);
    const rankB = getMediaRank(b);

    if (rankA !== rankB) {
      return rankA - rankB;
    }
    return a.localeCompare(b);
  });

  const sortedArticlesByMedia: Record<string, Article[]> = {};
  sortedMediaNames.forEach(name => {
    sortedArticlesByMedia[name] = articlesByMedia[name];
  });
  articlesByMedia = sortedArticlesByMedia;

  const regularMedia = Object.keys(articlesByMedia).filter(m => !isAggregator(m));
  const aggregatorMedia = Object.keys(articlesByMedia).filter(m => isAggregator(m));

  const date = data.date; 

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary pb-24 relative">
      {/* Loading Overlay for date changes */}
      <AnimatePresence>
        {loading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm"
          >
            <div className="flex flex-col items-center gap-4">
              <div className="w-10 h-10 border-4 border-text-primary border-t-transparent rounded-full animate-spin"></div>
              <div className="text-sm font-medium text-text-primary">Posodabljanje...</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Header currentDate={data.displayDate} />

      <main className="max-w-5xl mx-auto px-6 py-12 space-y-12">
        
        {/* Main Tabs */}
        <div className="flex justify-center">
          <div className="inline-flex p-1 bg-bg-secondary rounded-full border border-border">
            <button
              onClick={() => setMainTab('splosno')}
              className={`px-8 py-2.5 rounded-full text-sm font-medium transition-all ${
                mainTab === 'splosno' 
                  ? 'bg-white shadow-sm text-text-primary' 
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Splošno
            </button>
            <button
              onClick={() => setMainTab('nasprotniki')}
              className={`px-8 py-2.5 rounded-full text-sm font-medium transition-all ${
                mainTab === 'nasprotniki' 
                  ? 'bg-white shadow-sm text-text-primary' 
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Nasprotniki
            </button>
            <button
              onClick={() => setMainTab('podporniki')}
              className={`px-8 py-2.5 rounded-full text-sm font-medium transition-all ${
                mainTab === 'podporniki' 
                  ? 'bg-white shadow-sm text-text-primary' 
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Podporniki
            </button>
          </div>
        </div>

        {/* Summary Section */}
        <SummarySection 
          mainTab={mainTab} 
          currentDate={data.displayDate} 
          onPrevDay={handlePrevDay} 
          onNextDay={handleNextDay} 
          summary={data.summary}
          prevDate={data.prevDate}
          nextDate={data.nextDate}
        />

        {/* Sub Tabs */}
        <div className="flex items-center justify-between border-b border-border pb-4">
          <h3 className="text-2xl font-serif">Podrobna analiza</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setSubTab('teme')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                subTab === 'teme' ? 'bg-text-primary text-white' : 'bg-bg-secondary text-text-secondary hover:bg-border'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              Teme
            </button>
            <button
              onClick={() => setSubTab('clanki')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                subTab === 'clanki' ? 'bg-text-primary text-white' : 'bg-bg-secondary text-text-secondary hover:bg-border'
              }`}
            >
              <List className="w-4 h-4" />
              Članki
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="space-y-8">
          <AnimatePresence mode="wait">
            {subTab === 'teme' ? (
              <motion.div 
                key="teme"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {data.themes[mainTab]?.map((theme, idx) => (
                  <ThemeCard key={idx} theme={theme} date={date} />
                ))}
                {(!data.themes[mainTab] || data.themes[mainTab]?.length === 0) && (
                  <div className="text-center text-text-secondary py-12 bg-white rounded-2xl border border-border">
                    Ni tem za izbrano kategorijo.
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div 
                key="clanki"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-12"
              >
                {/* Regular Media */}
                <div className="space-y-8">
                  {regularMedia.map(medij => (
                    <MediaGroup key={medij} medij={medij} articles={articlesByMedia[medij]} mainTab={mainTab} date={data.date} />
                  ))}
                </div>

                {/* Aggregators */}
                {aggregatorMedia.length > 0 && (
                  <div className="pt-8 border-t border-border">
                    <h4 className="text-xl font-serif mb-6 text-text-secondary flex items-center gap-2">
                      <Newspaper className="w-5 h-5" />
                      Agregatorji novic
                    </h4>
                    <div className="space-y-8 opacity-80">
                      {aggregatorMedia.map(medij => (
                        <MediaGroup key={medij} medij={medij} articles={articlesByMedia[medij]} mainTab={mainTab} />
                      ))}
                    </div>
                  </div>
                )}
                
                {regularMedia.length === 0 && aggregatorMedia.length === 0 && (
                  <div className="text-center text-text-secondary py-12 bg-white rounded-2xl border border-border">
                    Ni člankov za izbrano kategorijo.
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
          <p className="text-center text-xs text-gray-400 font-light mt-3 tracking-widest uppercase">
            Built by{' '}
            <a href="https://kmecl.eu" target="_blank" rel="noopener noreferrer" className="underline hover:text-[#BC5A41]">Tim Kmecl</a> 2026
          </p>
        </div>
      </main>
    </div>
  );
};
