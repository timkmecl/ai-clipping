// backend/src/index.ts
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from "url";



dotenv.config();


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'dir', 'data');


const app = express();


// Middleware
const allowOrigins = [process.env.FRONTEND_URL || '', 'http://localhost:3000', 'http://192.168.0.100:3000'];
app.use(cors({
  origin: allowOrigins,
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(cookieParser());

const JWT_SECRET = process.env.JWT_SECRET!;

// Auth Middleware
const authenticate = (req: Request, res: Response, next: NextFunction) => {
  const token = req.cookies.auth_token;
  console.log("Authenticating request with token");
  if (!token) return res.status(401).json({ error: 'Unauthorized' });

  try {
    jwt.verify(token, JWT_SECRET);
    console.log("Authentication successful");
    next();
  } catch (err) {
    console.log("Authentication failed for token:", token, "Error:", err);
    res.status(401).json({ error: 'Invalid token' });
  }
};


// --- ROUTES ---

// Health check endpoint
app.get('/api/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 1. Login
app.post('/api/login', async (req: Request, res: Response) => {
  const { password } = req.body;
  const match = await bcrypt.compare(password, process.env.APP_PASSWORD!);
  if (match) {
    const token = jwt.sign({ authorized: true }, JWT_SECRET, { expiresIn: '7d' });
    
    res.cookie('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: process.env.NODE_ENV === 'production' ? 'none' : 'lax',
      maxAge: 365 * 24 * 60 * 60 * 1000,
    });

    console.log(process.env.NODE_ENV === 'production' ? "Production login successful" : "Development login successful");

    console.log("User authenticated successfully");
    return res.json({ success: true });
  }
  console.log("Failed login attempt with password.");
  res.status(401).json({ error: 'Wrong password' });
});


// 2. Verify (for Auto-login)
app.get('/api/verify', (req: Request, res: Response) => {
  console.log("Verifying authentication token...");
  const token = req.cookies.auth_token;
  if (!token) return res.json({ authenticated: false });
  
  try {
    jwt.verify(token, JWT_SECRET);
    console.log("Token is valid. User is authenticated.");
    res.json({ authenticated: true });
  } catch {
    console.log("Invalid token. User is not authenticated.");
    res.json({ authenticated: false });
  }
});


// 3. Logout
app.post('/api/logout', (req: Request, res: Response) => {
  res.clearCookie('auth_token');
  res.json({ success: true });
  console.log("User logged out, auth_token cookie cleared.");
});



// 4. Download Article PDF
app.get('/api/download/:date/:id', authenticate, (req: Request, res: Response) => {
  let { date, id } = req.params;
  // Ensure date and id are strings (in case they are string[])
  if (Array.isArray(date)) date = date[0];
  if (Array.isArray(id)) id = id[0];

  // 1. Construct the absolute path to the file
  // This points to: [your_project]/dir/data/[date]/[id].pdf
  const filePath = path.join(DATA_DIR, date, 'articles', `${id}`);

  console.log(`Attempting to send file at path: ${filePath}`);

  // 2. Check if the file exists before trying to send it
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    return res.status(404).json({ message: 'File not found' });
  }

  // 3. Set headers to ensure the browser opens it in a tab
  const options = {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `inline; filename="${id}.pdf"`
    }
  };


  // 4. Send the file
  res.sendFile(filePath, options, (err) => {
    if (err) {
      console.error('Error sending file:', err);
      res.status(500).end();
    }
  });
});


// 5 Get dates + analysis (optional date), returns dates + analysis for that date
app.post('/api/data', authenticate, (req: Request, res: Response) => {
  const { date } = req.body as { date?: string };

  console.log("Received request for data with date:", date);

  const datesPath = path.join(DATA_DIR, 'dates.json');
  if (!fs.existsSync(datesPath)) {
    console.error(`dates.json not found at path: ${datesPath}`);
    return res.status(500).json({ error: 'dates.json not found' });
  }

  const datesRaw = fs.readFileSync(datesPath, 'utf-8');
  const dates = JSON.parse(datesRaw);

  const chosenDate = date || (dates.length > 0 ? dates[dates.length - 1].id : undefined);
  if (!chosenDate) {
    console.error("No dates available in dates.json");
    return res.status(400).json({ error: 'No date available' });
  }

  const analysisPath = path.join(DATA_DIR, chosenDate, 'analysis.json');
  if (!fs.existsSync(analysisPath)) {
    console.error(`analysis.json not found for date ${chosenDate} at path: ${analysisPath}`);
    return res.status(404).json({ error: 'analysis.json not found for date' });
  }

  const analysisRaw = fs.readFileSync(analysisPath, 'utf-8');

  console.log(`Successfully read data for date: ${chosenDate}. Sending response.`);

  res.json({ dates, analysis: analysisRaw });
});


const PORT = process.env.PORT || 4102;
app.listen(PORT, () => console.log(`AI Clipping: Backend running at http://localhost:${PORT}`));