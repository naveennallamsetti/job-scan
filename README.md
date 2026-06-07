# job-scan

An automated job scanner, scraper, and customized resume/cover letter application dashboard built for AWS DevOps Engineers.

## Features
* **Concurrent Scanning**: Crawls 27 major job portals (LinkedIn, Indeed, Naukri, Wellfound, We Work Remotely, etc.) in parallel.
* **Auto-Apply & Document Tailoring**: Customizes resumes and cover letters specifically to match candidate skills and target JDs.
* **Portal-Based Displays**: Filters and groups matching job listings with status, progress, and success/failure diagnostics.
* **Enterprise Dashboard**: Sparkline metrics, interactive charts, and Recruiter Email interfaces.

## Tech Stack
* **Frontend**: React (Vite), Tailwind-free Vanilla CSS
* **Backend**: FastAPI (Python), `httpx`, `BeautifulSoup4`
* **Database**: SQLite
