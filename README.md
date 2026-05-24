# Career Autopsy - Why Careers Silently Fail

Career Autopsy is an AI-powered full-stack application designed to analyze career trajectories and identify silent failure points such as salary stagnation, burnout risks, automation pressure, and promotion ceilings. It delivers brutally honest and highly personalized insights based on user profile details and resume content.

## Key Features
- **Personalized Inputs:** Accepts job title, experience, country, tech stack, salary, work hours, company archetype, and target career goals.
- **Resume Upload & Parsing:** Supports PDF and TXT resume parsing, with built-in truncation to 3,000 characters to conserve Gemini free-tier tokens.
- **Interactive Risk Dashboard:** Displays metrics on burnout, stagnation, automation pressure, and industry decline exposure.
- **Autopsy Report & Sharing:** Generates custom autopsy verdicts (e.g. HIGH PLATEAU, CRITICAL THREAT) with shareable links and historical lookups.
- **Database Integration:** Persists reports using PostgreSQL (Neon DB) or SQLite.

## Technical Details
This project is basically built using a FastAPI backend paired with a simple, framework-free vanilla HTML, CSS, and JS frontend. To store the historical autopsy records, we have integrated a PostgreSQL database (like Neon DB) using SQLAlchemy, with a fallback to SQLite. The core intelligence runs on the Gemini AI API, which takes detailed user details—including an optional resume PDF parsed via the `pypdf` library—and returns a detailed risk assessment. We have also added a truncation logic of 3,000 characters for the resume text to ensure we do not hit the rate limits of the Gemini free tier. You can quickly run the application locally by installing the requirements and starting the Uvicorn development server on port 8000.

## Installation & Setup

1. **Clone/Navigate to the directory:**
   ```bash
   cd "f:\PY\Career Autopsy"
   ```

2. **Set up Environment Variables:**
   Create a `.env` file in the root directory (using the variables matching your setup):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   DATABASE_URL=postgresql://user:pass@host/dbname
   ```

3. **Install Dependencies:**
   Install required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   Start the FastAPI development server using Uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the App:**
   Open your browser and navigate to `http://127.0.0.1:8000`.
