import React from 'react';
import { motion } from 'motion/react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Summary } from '../types';

interface SummarySectionProps {
  mainTab: 'splosno' | 'nasprotniki' | 'podporniki';
  currentDate: string;
  onPrevDay: () => void;
  onNextDay: () => void;
  summary: Summary;
  prevDate: string | null;
  nextDate: string | null;
}

export const SummarySection: React.FC<SummarySectionProps> = ({ 
  mainTab, 
  currentDate, 
  onPrevDay, 
  onNextDay,
  summary,
  prevDate,
  nextDate
}) => {
  return (
    <motion.section 
      key={`summary-${mainTab}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-3xl p-8 md:p-12 shadow-sm border border-border"
    >
      <div className="flex items-center gap-3 mb-6">
        <button 
          onClick={onPrevDay} 
          disabled={!prevDate}
          className={`p-2 rounded-lg transition-colors ${!prevDate ? 'bg-bg-secondary text-text-secondary/30 cursor-not-allowed' : 'bg-bg-secondary hover:bg-border text-text-secondary'}`} 
          title={prevDate ? `Prejšnji dan (${prevDate})` : 'Ni prejšnjega dne'}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          {currentDate}
        </span>
        <button 
          onClick={onNextDay} 
          disabled={!nextDate}
          className={`p-2 rounded-lg transition-colors ${!nextDate ? 'bg-bg-secondary text-text-secondary/30 cursor-not-allowed' : 'bg-bg-secondary hover:bg-border text-text-secondary'}`} 
          title={nextDate ? `Naslednji dan (${nextDate})` : 'Ni naslednjega dne'}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
      <h2 className="text-4xl font-serif mb-6">
        {mainTab === 'splosno' ? 'Splošni pregled poročanja' : mainTab === 'nasprotniki' ? 'Pregled aktivnosti nasprotnikov' : 'Pregled aktivnosti podpornikov'}
      </h2>
      <div className="prose prose-lg text-text-secondary max-w-none leading-relaxed whitespace-pre-wrap">
        {summary[mainTab] || 'Ni podatkov za ta zavihek.'}
      </div>
    </motion.section>
  );
};
