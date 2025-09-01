\# JobApplication_AutomationAgent

\*\*JobApplication_AutomationAgent\*\* is an AI-powered end-to-end automation tool that helps job seekers automatically search, match, and apply for jobs on \[Dice](https://www.dice.com). It combines \*\*resume parsing, natural language processing (NLP), semantic similarity ranking, and browser automation\*\* with a user-friendly \*\*Streamlit UI\*\* and \*\*Flask API backend\*\*.

---

\## 🚀 Features

\- \*\*Resume Analysis \& Parsing\*\*

&nbsp; - Extracts text from PDF resumes.

&nbsp; - Uses GPT-powered analysis to identify \*\*top 2 job titles\*\* and \*\*top 2 key skills\*\* from your resume.

&nbsp;

\- \*\*Smart Job Search\*\*

&nbsp; - Builds a Dice search query from your resume keywords.

&nbsp; - Applies filters like \*\*Easy Apply\*\*, \*\*Third Party\*\*, \*\*Last 3 days\*\*, and \*\*100 results per page\*\*.

\- \*\*Semantic Similarity Matching\*\*

&nbsp; - Uses \*\*Sentence-Transformers (all-MiniLM-L6-v2)\*\* to generate embeddings for your resume and job descriptions.

&nbsp; - Computes cosine similarity scores to rank jobs by relevance.

&nbsp; - Applies only if similarity score ≥ configurable threshold (e.g., 0.80).

\- \*\*Automated Job Applications\*\*

&nbsp; - Logs into Dice with your credentials.

&nbsp; - Scrapes job postings and applies automatically via Playwright browser automation.

&nbsp; - Uploads your resume if required.

&nbsp; - Handles multi-step "Easy Apply" flows.

\- \*\*Tracking \& Logging\*\*

&nbsp; - Records applied job titles with timestamps into `job\_titles.txt`.

&nbsp; - Prevents duplicate logging of jobs.

\- \*\*Interactive UI\*\*

&nbsp; - Built with \*\*Streamlit\*\* for easy configuration:

&nbsp; - Upload resume

&nbsp; - Enter Dice credentials

&nbsp; - Set job location \& similarity threshold

&nbsp; - Trigger automation with one click

&nbsp; - Displays responses, status messages, and logs in real-time.

\- \*\*Modular Architecture\*\*

&nbsp; - Clean separation of:

&nbsp; - \*\*UI\*\* (`streamlit\_ui.py`)

&nbsp; - \*\*API Orchestrator\*\* (`app.py`)

&nbsp; - \*\*Automation Core\*\* (`DiceAutomation.py`)

---

\## 🧩 Project Workflow

1\. \*\*Upload Resume\*\* via Streamlit UI (PDF only).

2\. \*\*Flask API\*\* receives inputs and launches Playwright (Chromium).

3\. \*\*Resume Extraction\*\*: Text is extracted via PyPDF2.

4\. \*\*Keyword Generation\*\*: OpenAI GPT identifies job titles \& skills.

5\. \*\*Search Execution\*\*: Dice is queried with job titles, skills, and location filters.

6\. \*\*Job Collection\*\*: Job IDs scraped across multiple pages.

7\. \*\*Job Descriptions\*\*: Each job’s details are retrieved.

8\. \*\*Similarity Computation\*\*: Resume vs. job description embeddings compared.

9\. \*\*Application Logic\*\*: If similarity ≥ threshold, apply automatically.

10\. \*\*Tracking\*\*: Successful applications written to `job\_titles.txt`.

---

> ⚠️ \*\*Responsible Use:\*\* Job-site automation may violate Terms of Service. Use for learning or with permission.

---

\## 📂 Repository Structure

JobApplication_AutomationAgent/

│

├── app.py # Flask API orchestrator

├── streamlit_ui.py # Streamlit front-end for inputs and monitoring

├── DiceAutomation.py # Playwright + NLP automation functions

├── job_titles.txt # Log of applied jobs with timestamps

├── requirements.txt # Dependencies

├── .gitignore

├── README.md

└── LICENSE

---

\## 🔍 Function Breakdown (DiceAutomation.py)

\### `login(page, email, password)`

Logs into Dice dashboard with provided credentials.

\### `extract\_resume\_text(file\_path)`

Extracts raw text from a PDF resume.

\### `generate\_search\_query\_components(resume\_text)`

Uses OpenAI GPT to generate the \*\*top 2 job titles\*\* and \*\*top 2 skills\*\*.

\### `perform\_job\_search(page, search\_query, location)`

Executes search on Dice, applies filters (Easy Apply, Third Party, Last 3 Days, Page Size=100).

\### `extract\_job\_ids(page, max\_pages=20)`

Scrapes job IDs from search results across multiple pages.

\### `scrape\_job\_descriptions(page, job\_ids)`

Visits each job and scrapes its job description.

\### `preprocess\_text(text)`

Cleans and lemmatizes text (removes stopwords, special chars).

\### `compute\_similarity(resume\_text, job\_descriptions, job\_ids)`

Encodes text using Sentence-Transformers and computes cosine similarity.

\### `write\_job\_titles\_to\_file(page, job\_id, url)`

Logs job titles with timestamp into `job\_titles.txt` and triggers application flow.

\### `evaluate\_and\_apply(page, val)`

Attempts Easy Apply flow by clicking through job application steps.

\### `apply\_and\_upload\_resume(page, val)`

Handles resume uploads and final submission when required.

\### `logout\_and\_close(page, browser)`

Logs out from Dice and closes the browser.

---

\## 🏗 Architecture

\[Streamlit UI] ──(multipart/form-data POST)──> \[Flask API /automate-dice]

│

└──▶ \[Playwright Chromium Page]

├─ login()

├─ perform_job_search()

├─ extract_job_ids() ──▶ scrape_job_descriptions()

├─ compute_similarity(resume, jobs)

└─ write_job_titles_to_file() ─▶ evaluate_and_apply() ─▶ apply_and_upload_resume()

\- \*\*UI:\*\* `streamlit\_ui.py` — collects inputs and calls the Flask API.

\- \*\*API:\*\* `app.py` — orchestrates the whole job search/apply pipeline.

\- \*\*Automation Core:\*\* `DiceAutomation.py` — Playwright + NLP helper functions.

\- \*\*Log:\*\* `job\_titles.txt` — timestamped record of applied roles.

---

\## 🖥️ User Interface

The \*\*Streamlit UI\*\* (`streamlit\_ui.py`) provides:

\- Email, password, and location input fields.

\- Resume PDF upload.

\- A slider for similarity threshold (0.0 → 1.0).

\- A "Submit" button to start the automation.

\- Real-time feedback from Flask API responses.

---

\## 🔧 Installation

```bash

python -m venv .venv

\# Win: .venv\\Scripts\\activate    macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt

python -m playwright install



Requirements (key): Playwright, Flask, Sentence-Transformers (all-MiniLM-L6-v2), NLTK, PyPDF2, requests, Streamlit, openai.

app.py downloads NLTK stopwords + wordnet on first run.



Secrets:



Set OPENAI\_API\_KEY in your environment (used by generate\_search\_query\_components()).



Never commit real credentials or resumes.



---



▶️ Running the Application

1\) Start the Flask API

python app.py

\# Serves POST /automate-dice at http://127.0.0.1:5000



2\) Start the Streamlit UI (new terminal)

streamlit run streamlit\_ui.py

\# UI: http://localhost:8501



3\) Use the app



Fill Email, Password, Location (e.g., “Austin, TX”).



Upload Resume (PDF).



Set Threshold (e.g., 0.80).



Click Submit → watch responses/logs.



You can also hit the API directly with Postman/cURL (see API\_Request\_Postman.png).



---



📊 Example Outputs



job\_titles.txt



Java Developer - XYZ Corp - Austin, TX | Applied on: 2025-01-06 14:46:09 CST

Senior Full Stack Engineer - ABC Tech - Remote | Applied on: 2025-01-08 09:42:47 CST





Streamlit UI



Shows success/error responses



Displays JSON logs from API



---



🧠 How it works (function by function)



All functions live in DiceAutomation.py unless noted.



**login(page, email, password)**



Navigates to Dice login, fills credentials, and waits for dashboard. Uses robust selector/wait patterns and small sleeps to allow async UI loads.



**extract\_resume\_text(file\_path)**



Reads a PDF via PyPDF2 and concatenates page text. Raises if the PDF has no extractable text (scanned PDFs may fail).



**generate\_search\_query\_components(resume\_text)**



Calls OpenAI Chat Completions (model gpt-4) to return:



Job Titles: <title1>, <title2>

Skills: <skill1>, <skill2>





Parsed into two lists (2 titles, 2 skills) to build the Dice search query.



**perform\_job\_search(page, search\_query, location)**



Goes to /jobs



Fills job/keyword and location



Applies optional filters: Third Party, Easy Apply, Last 3 days



Sets page size to 100 where available



Waits for network idle to stabilize the DOM



**extract\_job\_ids(page, max\_pages=20, sleep\_after\_action=1.0)**



Finds job links with several CSS selectors and deduces a stable ID from:



data-\* attributes, or



URL patterns (/job-detail/<slug>-<id>, query ?jobId=...), or



fallback DOM id/href

Handles both Next/Load more and infinite scroll UIs.



**scrape\_job\_descriptions(page, job\_ids)**



Visits https://www.dice.com/job-detail/<id> and extracts the description from div.job-description (empty string if not found).



**preprocess\_text(text)**



Lowercases, strips non-letters, removes NLTK stopwords, and lemmatizes (WordNet).



**compute\_similarity(resume\_text, job\_descriptions, job\_ids)**



Encodes resume \& each job via SentenceTransformer('all-MiniLM-L6-v2')



Computes cosine similarity for each (resume, job) pair



Returns \[(job\_id, similarity\_score), ...]



In app.py, only pairs above the threshold are considered for apply.



**write\_job\_titles\_to\_file(page, job\_id, url)**



Opens the job, grabs document.title



Appends "Title | Applied on: <timestamp TZ>" to job\_titles.txt (de-duplicates titles)



Invokes evaluate\_and\_apply() to attempt an Easy Apply.



**evaluate\_and\_apply(page, val)**



Clicks Easy Apply inside the apply-button-wc web component via JS, then:



If the UI indicates an application is needed, calls apply\_and\_upload\_resume().



**apply\_and\_upload\_resume(page, val)**



Steps through the apply wizard:



Clicks Next



If “A resume is required to proceed”, it clicks Upload, sets file on <input type="file">, and confirms upload.



Clicks Submit to complete.



Note: This function expects a resume\_path to be available. In app.py the file is saved to UPLOAD\_FOLDER, but the path is not passed into DiceAutomation. If your Dice profile doesn’t already have a resume, wire resume\_path through (e.g., make it a parameter or a module-level variable before calling).



**logout\_and\_close(page, browser)**



Attempts to log out from the profile menu and closes the browser.



🧪 API (Flask)



POST /automate-dice (multipart/form-data)



Field		Type		Example		    Notes

email		text		user@domain.com	Dice login

password	text		••••••••		Dice password

location	text		Austin, TX	    Dice location filter

threshold	text		0.80	0.0–1.0 similarity threshold

resume		file/pdf	resume.pdf	    PDF only



Response: JSON { "status": "success" | "error", "message": "..." }



📁 Repository layout

.

├─ app.py                     # Flask API (orchestrator)

├─ streamlit\_ui.py            # Streamlit front-end

├─ DiceAutomation.py          # Playwright + NLP helpers

├─ job\_titles.txt             # Applied jobs log (title + timestamp)

├─ requirements.txt

├─ .gitignore

├─ API\_Request\_Postman.png

├─ Application\_Email\_Confirmation.png

├─ Recruiter\_Emails\_Received.png

└─ Streamlit\_ResponsiveUI.png



⚙️ Configuration tips



Headless mode: app.py launches with headless=False. Consider making it env-driven for CI:



headless = os.getenv("HEADLESS", "false").lower() == "true"

browser = playwright.chromium.launch(headless=headless)





Model caching: Load SentenceTransformer once per process (you already do).



Rate limiting: Add sleeps/backoff if Dice rate-limits or challenges login.



Persistent login: Consider Playwright storage state if you want to avoid logging in each run.



🛠 Troubleshooting



Playwright browser not found → python -m playwright install



Scanned PDFs (no text) → Recreate resume as true text PDF



OpenAI error → Ensure OPENAI\_API\_KEY is set; switch model name if needed



Selectors change → Update JOB\_LINK\_SELECTORS and description selector



Upload step fails → Pass resume\_path properly into apply\_and\_upload\_resume()



🗺 Roadmap



Pass resume\_path explicitly to upload function



Sort by similarity and apply top-K



Export applied results as CSV



Add retry/deduping \& throttling



Pluggable matchers (BM25 / semantic / RAG)



Multi-board adapters (Indeed/LinkedIn, etc.)

```
