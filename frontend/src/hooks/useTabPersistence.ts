import { useState, useEffect } from 'react';

let dashboardScrollPosition = 0;
let savedMainTab: 'splosno' | 'nasprotniki' | 'podporniki' = 'splosno';
let savedSubTab: 'teme' | 'clanki' = 'teme';

export function useTabPersistence() {
  const [mainTab, setMainTab] = useState<'splosno' | 'nasprotniki' | 'podporniki'>(savedMainTab);
  const [subTab, setSubTab] = useState<'teme' | 'clanki'>(savedSubTab);

  useEffect(() => {
    savedMainTab = mainTab;
  }, [mainTab]);

  useEffect(() => {
    savedSubTab = subTab;
  }, [subTab]);

  useEffect(() => {
    window.scrollTo(0, dashboardScrollPosition);
    
    const handleScroll = () => {
      dashboardScrollPosition = window.scrollY;
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return { mainTab, setMainTab, subTab, setSubTab };
}
