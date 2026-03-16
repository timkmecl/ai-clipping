# AI Clipping

AI-powered media monitoring and analysis tool that processes daily news PDFs, extracts article metadata using Google Gemini AI and summarizes the articles, and presents structured analysis of media coverage in a web interface.

## Project Structure

```
ai-clipping/
├── backend/              # Express.js API server (TypeScript)
├── frontend/             # React + Vite frontend (TypeScript + Tailwind)
├── pdf/                  # Python scripts for PDF processing and AI analysis
│   ├── process_daily_clipping.py   # Main processing pipeline
│   └── download_clipping.py         # Email-based PDF downloader
└── docker-compose.yml    # Production deployment config
```

## Tech Stack

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Motion, Lucide React
- **Backend**: Express.js, TypeScript, JWT authentication, bcrypt
- **PDF Processing**: Python 3, pypdf, Google Gemini AI (genai SDK)
- **Email**: imap-tools (Gmail IMAP)

## How It Works

### PDF Processing Pipeline

The Python scripts in `pdf/` process daily news PDFs through a 6-stage pipeline:

1. **PDF Splitting** (`split_pdf_full_process`): Splits the main PDF into individual article files by parsing table of contents links and extracting article metadata URIs from page headers

2. **TOC Processing** (`process_toc_files`): Sends each TOC page to Gemini to extract structured metadata (title, media, date, author, intro) for each article

3. **Article Analysis** (`analyze_articles`): For each article PDF, Gemini analyzes the content and extracts:
   - `splosno`: General summary and highlights
   - `nasprotniki`: Opponent narratives and arguments (if any)
   - `podporniki`: Supporter narratives and arguments (if any)

4. **Daily Summary** (`generate_daily_summary`): Creates an executive summary across all articles for the day

5. **Thematic Clustering** (`generate_thematic_aggregation`): Groups articles into specific themes for each perspective (general, opponents, supporters)

6. **Final Merge** (`merge_report_data`): Combines all data into a single `analysis.json` file

### Email Downloader

`download_clipping.py` runs as a daily cron job to:
1. Connect to Gmail via IMAP
2. Search for emails with subject "Porocilo SREBRNA NIT" and attachment "Dnevni kliping"
3. Download the PDF to the data directory
4. Automatically trigger the processing pipeline
5. Update `dates.json` with navigation data

### Web Interface

The frontend displays:
- **Three tabs**: Splošno (General), Nasprotniki (Opponents), Podporniki (Supporters)
- **Summary section**: Daily executive summary with navigation between dates
- **Theme cards**: Grouped articles by theme
- **Article list**: Individual articles grouped by media outlet
- **PDF viewer**: Inline PDF display for reading full articles

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- Google Gemini API key
- Gmail account (for automated downloads)

### Backend Setup

```bash
cd backend
npm install
# Configure your environment variables
npm run dev
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### PDF Processing (Manual)

Run from the `pdf` directory:

```bash
python process_daily_clipping.py
```

Configure via `.env`:
```
GENAI_API_KEY=your-gemini-api-key
```

### Email Downloader

For automated daily downloads, configure `.env`:
```
GMAIL_USER=your-email@gmail.com
GMAIL_PASS=your-app-password
```

Then run:
```bash
python download_clipping.py
```

Set up a cron job to run this daily.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Authenticate with password |
| GET | `/api/verify` | Check auth token validity |
| POST | `/api/logout` | Clear auth token |
| GET | `/api/download/:date/:id` | Serve article PDF file |
| POST | `/api/data` | Get dates and analysis data |
| GET | `/api/health` | Health check |

## Features

- **JWT Authentication**: Secure cookie-based auth with 7-day expiry
- **Three Perspectives**: Toggle between General, Opponents, Supporters views
- **Theme Clustering**: Articles automatically grouped by topic
- **Media Prioritization**: Major outlets (RTV, 24ur, Delo, etc.) shown first
- **Aggregator Detection**: Identifies and flags aggregated content
- **Date Navigation**: Browse historical daily reports
- **Inline PDF Viewer**: Read full articles without downloading

## Environment Variables

### Backend (`backend/.env`)

```bash
PORT=4102
JWT_SECRET=your-secret-key
FRONTEND_URL=http://localhost:3000
APP_PASSWORD=your-app-password
DATA_DIR=./dir/data
NODE_ENV=development
```

### PDF Processing (`pdf/.env`)

```bash
GENAI_API_KEY=your-gemini-api-key
GMAIL_USER=your-email@gmail.com
GMAIL_PASS=your-app-password
```

## Data Structure

Processed data is stored in:
```
data/
├── dates.json           # Navigation index
└── [date]/
    ├── analysis.json    # Final merged report
    ├── articles.json    # Article analysis data
    ├── themes.json      # Thematic clusters
    ├── summary.json     # Daily summary
    ├── metadata.json   # PDF splitting metadata
    ├── processed_metadata.json
    ├── TOC/             # Table of contents PDFs
    └── articles/        # Individual article PDFs
```

## License

MIT