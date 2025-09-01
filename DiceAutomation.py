from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import os
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
import time
import logging
import openai
from PyPDF2 import PdfReader
from datetime import datetime
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Load SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Login Function
def login(page, email, password):
    logger.info("Attempting to log in.")
    try:
        page.goto("https://www.dice.com/dashboard/login")
        page.wait_for_load_state("load")
        time.sleep(3)

        page.wait_for_selector('input[name="email"]', timeout=10000)
        page.fill('input[name="email"]', email)
        page.click('xpath=//*[@id="react-aria-:R2l7rkqfncq:"]')
        time.sleep(3)

        page.wait_for_selector('input[type="password"]', timeout=10000)
        page.fill('input[type="password"]', password)
        page.press('input[type="password"]', "Enter")
        page.wait_for_load_state("load")
        time.sleep(3)

        logger.info("Login successful.")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise

# Resume Text Extraction Function
def extract_resume_text(file_path):
    logger.info("Starting resume text extraction.")
    try:
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        if not text.strip():
            raise ValueError("PDF contains no extractable text.")
        logger.info("Resume text extraction completed successfully.")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise RuntimeError(f"Error extracting text from PDF: {e}")

# Search Query Components Generator Function
def generate_search_query_components(resume_text):
    logger.info("Generating search query components from resume text.")
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert resume analyzer and evaluator. "
                "Analyze resumes to generate top 2 most relevant job titles and top 2 most relevant skills that fit to the candidate's experience, background, and skillset to use in Dice search . "
                "Do not generate more than 2 job titles, and 2 skills. Do not use connection words like and or or to combine words together. Do not repeat same keywords in both job titles and skills. "
                "Respond in the following format:\n\n"
                "Job Titles: <Comma-separated job titles>\n"
                "Skills: <Comma-separated skills>"
            )
        },
        {
            "role": "user",
            "content": (
                f"Here is the text extracted from a resume:\n\n"
                f"{resume_text}\n\n"
                "Based on this resume, provide job titles and skills in the specified format."
            )
        }
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000,
            temperature=0.5
        )
        result = response.choices[0].message.content.strip()
        logger.info("OpenAI API response received.")
        print("API Response Content:", result)

        lines = result.split('\n')

        job_titles = []
        skills = []
        for line in lines:
            if "Job Titles:" in line:
                job_titles = line.split("Job Titles:")[-1].strip().split(', ')
            elif "Skills:" in line:
                skills = line.split("Skills:")[-1].strip().split(', ')

        if not job_titles or not skills:
            raise ValueError("API response did not contain expected job titles or skills.")

        logger.info(f"Generated Job Titles: {job_titles}")
        logger.info(f"Generated Skills: {skills}")
        return job_titles, skills

    except Exception as e:
        logger.error(f"Error generating search query components: {e}")
        raise RuntimeError(f"Error generating search query components: {e}")

# Job Search Function
def perform_job_search(page, search_query, location):
    logger.info("Performing job search.")
    try:
        # Be generous with timeouts on slow CDNs
        page.set_default_timeout(30000)

        # Go straight to Jobs, wait for JS to settle
        page.goto("https://www.dice.com/jobs", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        # --- Handle cookie/consent overlays (ignore if not present)
        for sel in [
            "button:has-text('Accept')",
            "button:has-text('I Accept')",
            "button:has-text('Agree')",
            "text=Accept All",
        ]:
            try:
                page.locator(sel).first.wait_for(timeout=2000)
                page.locator(sel).first.click()
                break
            except Exception:
                pass

        # --- Robust selectors for the two search boxes
        job_box = page.locator("input[placeholder='Job title, skill, company, keyword']").first
        loc_box = page.locator("input[placeholder='Location (ex. Denver, remote)']").first
        search_btn = page.locator("#submitSearch-button, button:has-text('Search')").first

        expect(job_box).to_be_visible()
        expect(job_box).to_be_enabled()
        expect(loc_box).to_be_visible()
        expect(loc_box).to_be_enabled()

        # Clear and fill
        job_box.click()
        job_box.fill("")
        job_box.fill(search_query)

        loc_box.click()
        loc_box.fill("")
        loc_box.fill(location)

        # Submit search
        expect(search_btn).to_be_enabled()
        search_btn.click()
        page.wait_for_url(re.compile(r"dice\.com/jobs.*"), timeout=30000)
        page.wait_for_load_state("networkidle")

        # Helper for safe filter clicks
        def safe_click(selector, timeout=7000, name_for_log=None):
            try:
                page.locator(selector).first.wait_for(timeout=timeout, state="visible")
                page.locator(selector).first.click()
                page.wait_for_load_state("networkidle")
                return True
            except Exception as e:
                logger.warning(f"Skipped filter {name_for_log or selector}: {e}")
                return False

        # --- Apply filters (skip quietly if they are missing)
        safe_click('button[aria-label="Filter Search Results by Third Party"]', name_for_log="Third Party")
        safe_click('button[aria-label="Filter Search Results by Easy Apply"]', name_for_log="Easy Apply")

        # Date posted: try direct text first, then fall back to opening the dropdown
        try:
            page.get_by_text("Last 3 days", exact=True).first.wait_for(timeout=6000)
            page.get_by_text("Last 3 days", exact=True).first.click()
            page.wait_for_load_state("networkidle")
        except Exception:
            try:
                page.get_by_role("button", name=re.compile("Date posted", re.I)).first.click()
                # Try option, radio, or text match
                sel_try = [
                    "role=option[name='Last 3 days']",
                    "role=menuitem[name='Last 3 days']",
                ]
                clicked = False
                for s in sel_try:
                    try:
                        page.get_by_role(*s.replace("role=", "").replace("[name='", "', name=").rstrip("]").split(",", 1)).click()  # quick-and-dirty parser
                        clicked = True
                        break
                    except Exception:
                        pass
                if not clicked:
                    page.get_by_text(re.compile(r"Last\s*3\s*days", re.I)).first.click()
                page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.warning(f"Date posted filter not applied: {e}")

        # Page size to 100 (the id often changes; match prefix)
        try:
            size_sel = page.locator("select[id^='pageSize']").first
            size_sel.wait_for(timeout=7000)
            # Some UIs use value, others use label—try both
            try:
                size_sel.select_option(value="100")
            except Exception:
                size_sel.select_option(label="100")
            page.wait_for_load_state("networkidle")
        except Exception as e:
            logger.warning(f"Could not set page size to 100: {e}")

        time.sleep(2)
        logger.info("Job search completed successfully.")
    except Exception as e:
        logger.error(f"Error during job search: {e}")
        raise

# Extract Job IDs
JOB_LINK_SELECTORS = [
    "a[data-cy='card-title-link']",
    "a[href*='/job-detail/']",
    "article [data-cy='card-title-link']",
    "article a:has(h5)",  # loose fallback
]

NEXT_BUTTON_SELECTORS = [
    "button:has-text('Next')",
    "li[aria-label='Next'] button",
    "li.pagination-next button",
    "button:has-text('Load more')",
    "button[aria-label='Next']",
]

RESULT_CONTAINER_SELECTORS = [
    "[data-cy='search-card']",
    "article[data-cy='search-card']",
    "article:has(a[href*='/job-detail/'])",
]

def _extract_job_id_from_attrs(elem):
    """Try multiple ways to get a stable job id; fallback to href or element id."""
    try:
        # Prefer data attributes if present
        for attr in ["data-job-id", "data-id", "data-jobid"]:
            val = elem.get_attribute(attr)
            if val:
                return val.strip()
        # Try from href patterns
        href = elem.get_attribute("href") or ""
        if href:
            # 1) ...?jobId=XXXXX
            m = re.search(r"[?&#](?:jobId|jobid)=([A-Za-z0-9\-_:]+)", href)
            if m:
                return m.group(1)
            # 2) /job-detail/<slug>-<id>
            m = re.search(r"/job-detail/(?:[^/?#]+)-([A-Za-z0-9]{6,})", href)
            if m:
                return m.group(1)
            # 3) last path segment
            m = re.search(r"/job-detail/([A-Za-z0-9\-_:]+)", href)
            if m:
                return m.group(1)
            # Fallback: whole href
            return href
        # Last resort: DOM id
        dom_id = elem.get_attribute("id")
        if dom_id:
            return dom_id.strip()
    except Exception:
        pass
    return None

def _wait_for_any_selector(page, selectors, timeout=15000):
    """Wait until any of the selectors appears visible."""
    last_error = None
    slice_timeout = max(1500, timeout // max(1, len(selectors)))
    for _ in range(2):  # two passes increases odds during slow loads
        for sel in selectors:
            try:
                page.locator(sel).first.wait_for(state="visible", timeout=slice_timeout)
                return sel
            except Exception as e:
                last_error = e
    if last_error:
        raise last_error

def extract_job_ids(page, max_pages=20, sleep_after_action=1.0):
    """
    Collect job IDs across the result list.
    Works with both infinite scroll and paginated UIs that Dice A/B tests.
    """
    job_ids = set()
    seen_links_count = 0
    stagnant_rounds = 0

    # Ensure results are present before starting
    _wait_for_any_selector(page, RESULT_CONTAINER_SELECTORS + JOB_LINK_SELECTORS, timeout=30000)

    for page_idx in range(max_pages):
        # Give time for lazy cards to render
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass
        time.sleep(sleep_after_action)

        # Grab links using multiple selectors
        links = []
        for sel in JOB_LINK_SELECTORS:
            try:
                links.extend(page.query_selector_all(sel))
            except Exception:
                continue

        # Extract IDs
        new_on_this_page = 0
        for a in links:
            jid = _extract_job_id_from_attrs(a)
            if jid and jid not in job_ids:
                job_ids.add(jid)
                new_on_this_page += 1

        # Heuristic to stop if nothing new is being added
        if len(job_ids) == seen_links_count:
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0
        seen_links_count = len(job_ids)

        # Try to advance: click Next/Load more if present; otherwise infinite scroll
        advanced = False
        for nsel in NEXT_BUTTON_SELECTORS:
            try:
                btn = page.locator(nsel).first
                # visible and not disabled
                btn.wait_for(state="visible", timeout=1500)
                disabled = False
                try:
                    disabled = btn.is_disabled()
                except Exception:
                    # check class for 'disabled'
                    try:
                        el = btn.element_handle()
                        if el:
                            disabled = el.evaluate("e => e.closest('li')?.classList?.contains('disabled') || e.classList?.contains('disabled')")
                    except Exception:
                        pass
                if not disabled:
                    btn.click()
                    advanced = True
                    break
            except Exception:
                continue

        if not advanced:
            # Infinite scroll fallback
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(sleep_after_action)
                # If still no new items after two stagnant rounds, we’re likely done
                if stagnant_rounds >= 2:
                    break
            except Exception:
                break
        else:
            # After clicking next, wait a moment and continue
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                pass
            time.sleep(sleep_after_action)

        # If next is disabled or we keep seeing nothing new, stop early
        if stagnant_rounds >= 3 and new_on_this_page == 0:
            break

    logger.info(f"Extracted {len(job_ids)} job IDs.")
    return list(job_ids)

# Scrape Job Descriptions
def scrape_job_descriptions(page, job_ids):
    if not isinstance(job_ids, list):
        logger.error("Job IDs should be passed as a list.")
    
    job_descriptions = []
    for job_id in job_ids:
        job_url = f"https://www.dice.com/job-detail/{job_id}"
        page.goto(job_url)
        time.sleep(2)
        job_desc_element = page.query_selector('div.job-description')
        if job_desc_element:
            #print(f"Scraped Job Description for ID {job_id}:\n{job_desc_element.inner_text()}\n")
            job_descriptions.append(job_desc_element.inner_text())
        else:
            job_descriptions.append("")  # Add empty description if not found
            print(f"No Job Description found for ID {job_id}.\n")
    return job_descriptions

# Preprocessing Function
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    stop_words = set(stopwords.words('english'))
    text = ' '.join(word for word in text.split() if word not in stop_words)
    lemmatizer = WordNetLemmatizer()
    text = ' '.join(lemmatizer.lemmatize(word) for word in text.split())
    return text

# Compute Similarity
def compute_similarity(resume_text, job_descriptions, job_ids):
    # Check if lengths match
    if len(job_ids) != len(job_descriptions):
        logger.error("Mismatch in lengths of job_ids and job_descriptions.")
        raise ValueError("The lengths of job_ids and job_descriptions do not match.")
    
    resume_text = preprocess_text(resume_text)
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    results = []

    # Iterate through job_ids and job_descriptions concurrently
    for job_id, job_desc in zip(job_ids, job_descriptions):
        job_desc = preprocess_text(job_desc)
        job_embedding = model.encode(job_desc, convert_to_tensor=True)
        similarity = util.cos_sim(resume_embedding, job_embedding).item()
        results.append((job_id, similarity))
        print(f"Job ID: {job_id}, Similarity Score: {similarity:.4f}")
    
    return results


def write_job_titles_to_file(page, job_id, url):
    logger.info("Writing job titles to file.")
    try:
        val = 0
        existing_titles = set()
        if os.path.exists('job_titles.txt'):
            with open('job_titles.txt', 'r') as file:
                existing_titles.update(file.read().splitlines())
        
        with open('job_titles.txt', 'a') as file:
            if job_id:
                job_url = f"https://www.dice.com/job-detail/{job_id}"
                try:
                    new_page = page.context.new_page()
                    new_page.goto(job_url)
                    new_page.wait_for_load_state("load")
                    time.sleep(3)

                    job_title = new_page.evaluate("document.title")
                    
                    current_time = datetime.now().astimezone()
                    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')
                    
                    if job_title not in existing_titles:
                        file.write(f"{job_title} | Applied on: {formatted_time}\n")
                        logger.info(f"Processed job ID: {job_id} with title: {job_title}")
                    else:
                        logger.info(f"Skipped duplicate job title: {job_title}")
                    
                    new_page.wait_for_selector('apply-button-wc')
                    val += 1
                    evaluate_and_apply(new_page, val)
                except Exception as e:
                    logger.error(f"Error processing job ID {job_id}: {e}")
    except Exception as e:
        logger.error(f"Error writing job titles to file: {e}")

def evaluate_and_apply(page, val):
    js_script = """
        let value = 0; 
        const applyButtonWc = document.querySelector('apply-button-wc');

        if (applyButtonWc) {
            const shadowRoot = applyButtonWc.shadowRoot;
            const easyApplyButton = shadowRoot.querySelector('button.btn.btn-primary');

            if (easyApplyButton) {
                easyApplyButton.click();
                const applicationSubmitted = shadowRoot.querySelector('application-submitted');
                if (applicationSubmitted) {
                    const appTextElement = applicationSubmitted.shadowRoot.querySelector('p.app-text');
                    if (appTextElement && appTextElement.textContent.includes('Application Submitted')) {
                        value = 0;
                    } else {
                        value = 1;
                    }
                } else {
                    value = 1;
                }
            }
        } else {
            value = 0;
        }
        value;  // Return value for evaluation in Python
    """
    returned_value = page.evaluate(js_script)

    if returned_value == 1:
        apply_and_upload_resume(page, val)


def apply_and_upload_resume(page, val):
    page.wait_for_load_state("load")
    time.sleep(3)
    page.wait_for_selector('button.seds-button-primary.btn-next')
    next_button = page.query_selector('button.seds-button-primary.btn-next')

    if next_button:
        next_button.click()
        page.wait_for_load_state("load")
        time.sleep(3)

        resume_upload_error = "A resume is required to proceed"
        page_content = page.evaluate("document.body.textContent")

        if resume_upload_error in page_content:
            print("A resume is required to proceed.")
            print("Resume is missing. Uploading resume...")

            page.wait_for_load_state("load")
            time.sleep(3)
            page.wait_for_selector('button[data-v-746be088]')
            upload_button = page.query_selector('button[data-v-746be088]')

            if upload_button:
                upload_button.click()
                file_path = resume_path

                page.wait_for_selector('input[type="file"]')
                input_file = page.query_selector('input[type="file"]')

                if input_file:
                    input_file.set_input_files(file_path)
                    page.wait_for_load_state("load")
                    time.sleep(3)

                    page.wait_for_selector('span[data-e2e="upload"]')
                    upload_confirm_button = page.query_selector('span[data-e2e="upload"]')

                    if upload_confirm_button:
                        upload_confirm_button.click()
                        page.wait_for_load_state("load")
                        time.sleep(3)

                        page.wait_for_selector('button.seds-button-primary.btn-next')
                        next_button = page.query_selector('button.seds-button-primary.btn-next')

                        if next_button:
                            next_button.click()
                            page.wait_for_load_state("load")
                            time.sleep(3)
                        else:
                            print("Next button after uploading resume not found.")
                            return
                    else:
                        print("Resume upload confirmation button not found.")
                        return
                else:
                    print("File input element not found.")
                    return
            else:
                print("Upload button not found.")
                return
        else:
            print("Resume already uploaded. Proceeding to submit.")

        page.wait_for_selector('button.seds-button-primary.btn-next', timeout=5000)
        submit_button = page.query_selector('button.seds-button-primary.btn-next')

        if submit_button and "Submit" in submit_button.text_content():
            submit_button.click()
            print(f"Job application submitted") #for job ID: {val}")
            page.close()
        else:
            print("Submit button not found or incorrect selector.")
    else:
        print("Next button not found.")


def logout_and_close(page, browser):
    logger.info("Logging out and closing browser.")
    try:
        page.goto("https://www.dice.com/dashboard/login")
        menu_settings = page.query_selector('//*[@data-id="menu-settings"]')
        if menu_settings:
            menu_settings.click()
            time.sleep(3)
            menu_logout = page.query_selector('//*[@data-id="menu-logout"]')
            if menu_logout:
                menu_logout.click()
                time.sleep(3)
        browser.close()
        logger.info("Logged out and browser closed successfully.")
    except Exception as e:
        logger.error(f"Error during logout: {e}")

