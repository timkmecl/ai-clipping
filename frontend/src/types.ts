export interface Article {
  id: string;
  naslov: string;
  medij: string;
  datum: string;
  avtor?: string;
  url?: string;
  oznaka: string[];
  intro: string;
  contents: {
    splosno: {
      povzetek: string;
      highlights: string[];
    };
    nasprotniki: {
      povzetek: string;
      highlights: string[];
    } | null;
    podporniki?: {
      povzetek: string;
      highlights: string[];
    } | null;
  };
}

export interface ThemeItem {
  naslov: string;
  povzetek: string;
  highlights: string[];
  ids: string[];
  mediji: string[];
}

export interface ThemesData {
  splosno: ThemeItem[];
  nasprotniki: ThemeItem[];
  podporniki?: ThemeItem[];
}

export interface Summary {
  splosno: string;
  nasprotniki: string;
  podporniki?: string;
}

export interface ClippingData {
  date: string;
  displayDate: string;
  prevDate: string | null;
  nextDate: string | null;
  summary: Summary;
  articles: Article[];
  themes: ThemesData;
}
