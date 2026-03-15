import { ClippingData } from '../types';

export class ApiService {
  static async fetchClippingData(date?: string): Promise<ClippingData> {
    const res = await fetch(`${process.env.API_URL}/data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date }),
      credentials: 'include',
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.status}`);
    }

    const { dates, analysis: analysisRaw } = await res.json();
    const analysis = JSON.parse(analysisRaw);

    return {
      date: date || dates[dates.length - 1]?.id,
      displayDate: (dates.find((d: any) => d.id === (date || dates[dates.length - 1]?.id)) || {}).date,
      prevDate: (dates.find((d: any) => d.id === (date || dates[dates.length - 1]?.id)) || {}).prev,
      nextDate: (dates.find((d: any) => d.id === (date || dates[dates.length - 1]?.id)) || {}).next,
      summary: analysis.summary,
      articles: analysis.articles,
      themes: analysis.themes,
    };
  }
}