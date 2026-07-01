# Research Network Hub

A comprehensive web application for graduate school applicants in clinical psychology to discover programs, find Principal Investigators (PIs), generate personalized application materials, and track their application progress.

## Overview

Research Network Hub is an integrated platform that helps prospective graduate students in clinical psychology:

- **Discover Programs**: Find and rank APA/PCSAS accredited clinical psychology programs based on research fit
- **Find Researchers**: Identify Principal Investigators matching your research interests and specialties
- **Generate Application Materials**: Create personalized emails and statements of interest using AI
- **Track Applications**: Manage your application pipeline from initial interest through decisions

The platform integrates with multiple academic data sources including OpenAlex, ClinicalTrials.gov, and NIH Reporter to provide comprehensive research insights.

## Features

### 1. User Profile Management
Create and manage your academic profile including:
- Research interests and specialties
- CV/accomplishments (upload or paste text)
- Publications and presentations
- Program type preferences
- Geographic preferences

Your profile is used to personalize program recommendations and generate application materials.

### 2. Program Discovery
Discover clinical psychology programs ranked by research fit:
- **Comprehensive Database**: Aggregates APA and PCSAS accredited programs
- **Research-Based Matching**: Finds programs with relevant research papers matching your interests
- **Intelligent Ranking**: Programs ranked by:
  - Research interest overlap
  - Faculty match quality
  - University research strength
  - Geographic preferences
- **Detailed Research Insights**: View top researchers, relevant papers, and research summaries for each program
- **Direct Integration**: Add programs directly to your tracker

### 3. Draft & Research Tool
Generate personalized application materials and gather PI research:
- **AI-Powered Draft Generation**: Create personalized emails and statements of interest using Google Gemini
- **PI Research Gathering**: Automatically collect:
  - Recent publications with summaries
  - Clinical trials
  - NIH-funded projects
  - PI research summaries
- **Multiple Formats**: Generate emails or statements with customizable word counts
- **Version History**: Track and restore previous drafts
- **Export Options**: Copy to clipboard, open in Gmail, Google Docs, or download as text

### 4. Program Tracker
Track your application progress:
- **Application Pipeline**: Track programs through stages (Interested → Applied → Interview → Accepted/Rejected/Waitlisted)
- **Deadline Management**: Set and track application deadlines, interview dates, and decision dates
- **Notes & Details**: Add notes, advisor information, and other details for each program
- **Status Filtering**: Filter programs by application status
- **Timeline View**: Visual timeline of your application cycle

### 5. PI Finder Agent
Find Principal Investigators matching your research interests:
- **Specialty Matching**: Search by research specialties (e.g., memory, trauma, depression)
- **Technique Filtering**: Filter by research techniques (e.g., MRI, EEG, fMRI)
- **Geographic Filtering**: Filter by country
- **Relevance Ranking**: Results ranked by research alignment and relevance

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Dependencies**: Managed via Pipenv
- **APIs Integrated**:
  - OpenAlex (academic papers and researchers)
  - ClinicalTrials.gov (clinical trials data)
  - NIH Reporter (NIH-funded projects)
  - Google Gemini (AI text generation)

### Frontend
- **Language**: TypeScript
- **Build Tool**: Webpack
- **Styling**: Vanilla CSS
- **No Framework**: Lightweight vanilla TypeScript for optimal performance

## Setup Instructions

### Prerequisites

- **Python 3.11** or higher
- **Node.js** and npm
- **Pipenv** (Python package manager)
- **Google Gemini API Key** (for AI features)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pipenv install
   ```

3. **Activate the virtual environment:**
   ```bash
   pipenv shell
   ```

4. **Configure Gemini API Key** (see [Gemini API Key Configuration](#gemini-api-key-configuration) below)

5. **Start the backend server:**
   ```bash
   pipenv run start
   ```

   The backend will start on `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

   The frontend will start on `http://localhost:9000` and automatically proxy API requests to the backend.

### Verification

After starting both servers:

1. **Backend**: Visit `http://127.0.0.1:8000/docs` to see the API documentation
2. **Frontend**: Visit `http://localhost:9000` to access the web application

## Gemini API Key Configuration

The application uses Google Gemini 2.0 Flash for AI-powered features (draft generation, profile analysis). You must configure an API key for these features to work.

### Getting an API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### Setting the API Key

You can set the API key in two ways:

#### Option 1: Environment Variable (Recommended)

Create a `.env` file in the `backend` directory:

```bash
cd backend
touch .env
```

Add your API key to the `.env` file:

```
GEMINI_API_KEY=your_api_key_here
```

The application will automatically load this when it starts.

#### Option 2: System Environment Variable

Set the environment variable before starting the server:

**On macOS/Linux:**
```bash
export GEMINI_API_KEY=your_api_key_here
pipenv run start
```

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
pipenv run start
```

### Hot Swapping API Keys

If you need to change your API key (e.g., due to quota limits or key rotation):

1. **Update the `.env` file:**
   ```bash
   # Edit backend/.env
   GEMINI_API_KEY=your_new_api_key_here
   ```

2. **Restart the backend server:**
   - Stop the current server (Ctrl+C)
   - Start it again: `pipenv run start`

The new API key will be loaded automatically. No code changes are required.

**Note**: The application includes a fallback API key in the code, but it's recommended to use your own key via environment variable for production use and to avoid quota issues.

### API Key Validation

The application validates the API key on startup. If the key is invalid or expired, you'll see a warning in the logs, but the server will still start. AI features will fail with clear error messages if the key is invalid.

## Project Structure

```
re-search/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents (PI finder, research gatherer, etc.)
│   │   ├── models/          # Pydantic data models
│   │   ├── routes/          # FastAPI route handlers
│   │   ├── scrapers/        # Web scrapers (PCSAS, etc.)
│   │   ├── storage/         # In-memory storage (profiles, etc.)
│   │   ├── utils/           # Utility functions (API clients, parsers, etc.)
│   │   └── main.py          # FastAPI application entry point
│   ├── Pipfile              # Python dependencies
│   └── .env                 # Environment variables (create this)
├── frontend/
│   ├── src/                 # TypeScript source files
│   ├── public/              # Static files and built bundle
│   ├── package.json         # Node.js dependencies
│   └── webpack.config.js    # Webpack configuration
└── README.md
```

## API Integrations

### OpenAlex API
- **Purpose**: Academic papers, researchers, and institutions
- **Authentication**: None required (public API)
- **Rate Limits**: Be mindful of rate limits; the application includes caching
- **Usage**: Program discovery, PI research gathering, paper search

### ClinicalTrials.gov API
- **Purpose**: Clinical trial information
- **Authentication**: None required (public API)
- **Usage**: PI research gathering, finding relevant clinical trials

### NIH Reporter API
- **Purpose**: NIH-funded research projects
- **Authentication**: None required (public API)
- **Usage**: PI research gathering, finding NIH-funded projects

### Google Gemini API
- **Purpose**: AI-powered text generation (drafts, summaries)
- **Authentication**: API key required (see [Gemini API Key Configuration](#gemini-api-key-configuration))
- **Usage**: Draft generation, profile analysis, research summaries
- **Model**: Gemini 2.0 Flash

## Usage Guide

### Creating a User Profile

1. Navigate to the "User Profile" tab
2. Fill in your research interests, program type, and other preferences
3. Upload or paste your CV/accomplishments
4. Click "Create Profile"

Your profile is used throughout the application to personalize recommendations and generate materials.

### Discovering Programs

1. Ensure you have a user profile with research interests
2. Navigate to the "Program Discovery" tab
3. Click "Load Programs"
4. Browse ranked programs with research fit scores
5. View detailed research information for each program
6. Add programs directly to your tracker

### Generating Application Materials

1. Navigate to the "Draft & Research" tab
2. Enter PI information (name, ORCID, or OpenAlex ID)
3. Click "Gather Research" to collect PI's publications, trials, and projects
4. Review the PI summary and research
5. Select format (Email or Statement)
6. Optionally provide an initial draft
7. Click "Generate Draft" to create personalized content
8. Edit, save versions, and export as needed

### Tracking Applications

1. Navigate to the "Program Tracker" tab
2. Click "Add Program" or add from Program Discovery
3. Fill in program details and set status
4. Update status as you progress through the application cycle
5. Use filters to view programs by status

## Caching

The application implements caching for:

- **Program Data**: APA and PCSAS program lists (cached for 30 days)
- **OpenAlex API Responses**: Paper searches, author data (cached for 30 days)
- **Research Interest Searches**: Cached to avoid redundant API calls

Cache files are stored in `backend/.cache/` and can be cleared by deleting this directory.

## Development

### Running in Development Mode

Both backend and frontend support hot reloading:

- **Backend**: Uses `uvicorn --reload` (automatic via `pipenv run start`)
- **Frontend**: Uses webpack-dev-server with hot module replacement

### Testing

**Backend tests:**
```bash
cd backend
pipenv run test
```

**Format code:**
```bash
cd backend
pipenv run format
```

**Lint code:**
```bash
cd backend
pipenv run lint
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

The built bundle will be in `frontend/public/bundle.js` during dev, or `frontend/dist/` for production/GitHub Pages builds.

## Deployment

Deploy the backend to **Render (free tier)** and the frontend to **GitHub Pages**. Full instructions: **[DEPLOY.md](DEPLOY.md)**.

## Troubleshooting

### Gemini API Errors

If you see errors about invalid API keys:
1. Verify your API key is correct in `.env` or environment variable
2. Check that the key hasn't expired or been revoked
3. Ensure you've restarted the server after changing the key
4. Check the backend logs for detailed error messages

### Program Discovery Not Working

If program discovery returns no results:
1. Ensure you have a user profile with research interests
2. Check that the backend is running and accessible
3. Verify OpenAlex API is accessible (check network connectivity)
4. Check backend logs for API errors

### Frontend Not Connecting to Backend

If the frontend can't reach the backend:
1. Verify the backend is running on port 8000
2. Check that the webpack proxy is configured correctly (should be in `webpack.config.js`)
3. Check browser console for CORS or network errors

## License

[Add your license information here]

## Contributing

[Add contributing guidelines if applicable]
