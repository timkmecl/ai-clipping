import { ClippingData } from '../types';
import { analysis, dates } from '../mockData';

export class ApiService {
  /**
   * Fetches clipping data for a specific date or the current date if not provided.
   * In a real implementation, this would be a POST request to the API.
   */
  static async fetchClippingData(date?: string): Promise<ClippingData> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Mocking date logic:
    // If no date provided, we assume it's "18. 11. 2025"
    // We'll mock that 17. 11. 2025 is the previous day and 19. 11. 2025 is the next day
    // But if it's 17. 11. 2025, then prevDate is null
    // If it's 19. 11. 2025, then nextDate is null
    
    // const current = date || "18. 11. 2025";
    // let prev: string | null = "17. 11. 2025";
    // let next: string | null = "19. 11. 2025";

    // if (current === "17. 11. 2025") {
    //   prev = null;
    // } else if (current === "19. 11. 2025") {
    //   next = null;
    // }

    // const current = "14. 11. 2025";
    // const prev = null;
    // const next = null;

    const datesParsed = JSON.parse(dates);

    // // last item in dates is the most recent one
    // const current = date || datesParsed[datesParsed.length - 1].date;
    // const currentIndex = datesParsed.findIndex((d: { date: string }) => d.date === current);
    // const prev = currentIndex > 0 ? datesParsed[currentIndex - 1].date : null;
    // const next = currentIndex < datesParsed.length - 1 ? datesParsed[currentIndex + 1].date : null;

    const currentId = date || datesParsed[datesParsed.length - 1].id;
    const currentIndex = datesParsed.findIndex((d: { id: string }) => d.id === currentId);
    const currentDate = datesParsed[currentIndex];
    const prev = currentDate.prev;
    const next = currentDate.next;
    const displayDate = currentDate.date;

    const data = JSON.parse(analysis);
    const summary = data.summary;
    const themes = data.themes;
    const articles = data.articles;

    // console.log(articles);


    return {
      date: currentId,
      displayDate: displayDate,
      prevDate: prev,
      nextDate: next,
      summary: summary,
      articles: articles,
      themes: themes
    };
  }
}
