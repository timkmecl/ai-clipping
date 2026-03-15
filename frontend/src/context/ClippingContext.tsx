import React, { createContext, useContext, useState, useCallback } from 'react';
import { ClippingData } from '../types';
import { ApiService } from '../services/apiService';

interface ClippingContextType {
  data: ClippingData | null;
  loading: boolean;
  loadData: (date?: string) => Promise<void>;
}

const ClippingContext = createContext<ClippingContextType | undefined>(undefined);

export const ClippingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [data, setData] = useState<ClippingData | null>(null);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async (date?: string) => {
    setLoading(true);
    try {
      const result = await ApiService.fetchClippingData(date);
      setData(result);
    } catch (error) {
      console.error('Error loading clipping data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <ClippingContext.Provider value={{ data, loading, loadData }}>
      {children}
    </ClippingContext.Provider>
  );
};

export const useClipping = () => {
  const context = useContext(ClippingContext);
  if (context === undefined) {
    throw new Error('useClipping must be used within a ClippingProvider');
  }
  return context;
};
