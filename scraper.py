"""
Job Scraper - Indeed Direct
Resume Audit Study - Tech Demo

Scrapes job listings directly from Indeed using Playwright.
Extracts title, company, location, description, salary, and posting URL.

NOTE: This approach violates Indeed's ToS. The proposal recommends a
third-party data provider for production use. This demo is for feasibility
testing only.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from playwright.sync_api import sync_playwright, Page, TimeoutError as PwTimeout


@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    description: str
    posting_url: str | None
    date_posted: str | None
    salary: str | None
    job_id: str | None


def build_indeed_url(query: str, location: str, start: int = 0) -> str:
    """Build an Indeed search URL."""
    q = query.replace(" ", "+")
    loc = location.replace(" ", "+")
    return f"https://www.indeed.com/jobs?q={q}&l={loc}&start={start}"


def scrape_indeed(
    query: str,
    location: str,
    max_jobs: int = 10,
    headless: bool = False,
) -> list[JobPosting]:
    """
    Scrape job listings directly from Indeed.

    Args:
        query: Job search query (e.g., "registered nurse")
        location: Location (e.g., "Dallas, TX")
        max_jobs: Maximum number of jobs to collect
        headless: Run browser in headless mode (False helps avoid detection)
    """
    jobs: list[JobPosting] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        url = build_indeed_url(query, location)
        print(f"  Navigating to: {url}")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except PwTimeout:
            print("  [!] Page load timed out")
            browser.close()
            return jobs

        time.sleep(3)  # Let page settle

        # Check for actual CAPTCHA blocking (not just page content mentioning it)
        page_text = page.content()
        blocked_signals = [
            "unusual traffic from your computer",
            "please verify you are a human",
            "recaptcha" in page_text.lower() and "jobsearch" not in page_text.lower(),
        ]
        if any(
            isinstance(s, bool) and s or
            isinstance(s, str) and s in page_text.lower()
            for s in blocked_signals
        ):
            print("  [!] Indeed detected automation — CAPTCHA triggered.")
            print("  [!] Saving screenshot to debug_indeed.png")
            page.screenshot(path="debug_indeed.png")
            browser.close()
            return jobs

        # Save screenshot for debugging regardless
        page.screenshot(path="debug_indeed.png")

        # Find job cards on the search results page
        # Indeed uses various selectors — try the common ones
        card_selectors = [
            'div.job_seen_beacon',
            'div[class*="jobsearch-ResultsList"] div[class*="result"]',
            'a[data-jk]',
            'td.resultContent',
        ]

        cards = []
        for sel in card_selectors:
            cards = page.query_selector_all(sel)
            if cards:
                print(f"  Found {len(cards)} job cards (selector: {sel})")
                break

        if not cards:
            print("  [!] No job cards found. Indeed may have changed their DOM.")
            print("  [!] Saving screenshot to debug_indeed.png")
            page.screenshot(path="debug_indeed.png")
            # Try to get whatever is on the page
            print(f"  Page title: {page.title()}")
            browser.close()
            return jobs

        # Process each card
        for i, card in enumerate(cards[:max_jobs]):
            try:
                job = _extract_from_card(page, card, i)
                if job:
                    jobs.append(job)
                    salary_str = f" | {job.salary}" if job.salary else ""
                    print(f"  [{i+1}] {job.title} @ {job.company}{salary_str}")
            except Exception as e:
                print(f"  [{i+1}] Error extracting: {e}")

        # Get descriptions by navigating to each job's detail page
        print(f"\n  Fetching full descriptions from detail pages...")

        for i, job in enumerate(jobs):
            if not job.job_id:
                print(f"  [{i+1}] No job ID — skipping")
                continue
            try:
                detail_url = f"https://www.indeed.com/viewjob?jk={job.job_id}"
                page.goto(detail_url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)

                # Debug: save screenshot of first detail page
                if i == 0:
                    page.screenshot(path="debug_detail.png")

                desc = _extract_description(page)
                if desc:
                    job.description = desc
                    print(f"  [{i+1}] Got description ({len(desc)} chars)")
                else:
                    # Dump all div IDs for debugging
                    if i == 0:
                        ids = page.evaluate("""
                            () => Array.from(document.querySelectorAll('div[id]'))
                                .map(el => ({id: el.id, textLen: el.innerText.length}))
                                .filter(x => x.textLen > 50)
                                .slice(0, 20)
                        """)
                        print(f"  [{i+1}] No description found. Div IDs with text: {ids}")
                    else:
                        print(f"  [{i+1}] No description found")
            except Exception as e:
                print(f"  [{i+1}] Error: {e}")

        browser.close()

    return jobs


def _extract_from_card(page: Page, card, index: int) -> JobPosting | None:
    """Extract basic job info from a search result card."""

    # Title
    title_el = card.query_selector('h2 a, h2 span, a[data-jk] span')
    title = title_el.inner_text().strip() if title_el else None

    # Company
    company_el = card.query_selector(
        'span[data-testid="company-name"], '
        'span.companyName, '
        'span[class*="company"]'
    )
    company = company_el.inner_text().strip() if company_el else None

    # Location
    loc_el = card.query_selector(
        'div[data-testid="text-location"], '
        'div.companyLocation, '
        'div[class*="location"]'
    )
    location = loc_el.inner_text().strip() if loc_el else None

    # Salary (not always present)
    salary = None
    salary_el = card.query_selector(
        'div[class*="salary"], '
        'span[class*="salary"], '
        'div[data-testid*="salary"]'
    )
    if salary_el:
        salary = salary_el.inner_text().strip()

    # Job link and ID
    link_el = card.query_selector('a[data-jk], h2 a')
    posting_url = None
    job_id = None
    if link_el:
        href = link_el.get_attribute("href") or ""
        jk = link_el.get_attribute("data-jk")
        if href:
            if href.startswith("/"):
                posting_url = f"https://www.indeed.com{href}"
            else:
                posting_url = href
        job_id = jk

    # Date posted
    date_el = card.query_selector('span.date, span[class*="date"]')
    date_posted = date_el.inner_text().strip() if date_el else None

    if not title:
        return None

    return JobPosting(
        title=title,
        company=company or "Unknown",
        location=location or "Unknown",
        description="",  # Populated later from detail page
        posting_url=posting_url,
        date_posted=date_posted,
        salary=salary,
        job_id=job_id,
    )


def _extract_description(page: Page) -> str | None:
    """Extract full job description from Indeed's side panel or detail page."""
    selectors = [
        'div#jobDescriptionText',
        'div[id="jobDescriptionText"]',
        'div[class*="jobDescription"]',
        'div[id*="jobDescription"]',
        # Side panel selectors
        'div.jobsearch-JobComponent-description',
        'div[class*="JobComponent-description"]',
        'div.jobsearch-jobDescriptionText',
        # Iframe content
        'iframe#vjs-container-iframe',
    ]
    for sel in selectors:
        el = page.query_selector(sel)
        if el:
            tag = el.evaluate("el => el.tagName")
            if tag == "IFRAME":
                # Indeed sometimes loads descriptions in an iframe
                frame = el.content_frame()
                if frame:
                    body = frame.query_selector('body, div#jobDescriptionText')
                    if body:
                        text = body.inner_text().strip()
                        if len(text) > 50:
                            return text[:5000]
            else:
                text = el.inner_text().strip()
                if len(text) > 50:
                    return text[:5000]

    # Last resort: try to find any large text block in the right pane
    right_pane = page.query_selector('div.jobsearch-RightPane, div[class*="RightPane"]')
    if right_pane:
        text = right_pane.inner_text().strip()
        if len(text) > 100:
            return text[:5000]

    return None


def run_scraper_demo():
    """Run the scraper and pipe results through dedup + education extraction."""
    from employer_dedup import EmployerRegistry
    from education_extractor import extract_education

    print("=" * 70)
    print("INDEED SCRAPER DEMO -> Dedup -> Education Extraction")
    print("=" * 70)
    print()

    jobs = scrape_indeed(
        query="registered nurse",
        location="Dallas, TX",
        max_jobs=10,
        headless=False,  # Visible browser helps avoid detection
    )

    if not jobs:
        print("\n  No jobs scraped. Check debug_indeed.png for what happened.")
        print("  Indeed aggressively blocks automated access — this is expected.")
        print("  The proposal recommends a third-party data provider for production.")
        return

    print(f"\n  Scraped {len(jobs)} jobs. Running through pipeline...\n")
    print("=" * 70)
    print("PIPELINE: Employer Dedup + Education Extraction")
    print("=" * 70)

    registry = EmployerRegistry()

    for i, job in enumerate(jobs):
        match = registry.resolve(job.company, "Dallas-Fort Worth")
        edu = extract_education(job.description)
        resume_count = 3 if edu.level.value == "unspecified" else 2

        print(f"\n  [{i+1}] {job.title}")
        print(f"      Company (raw):       {job.company}")
        print(f"      Company (canonical): {match.matched_employer.canonical_name} "
              f"[ID:{match.matched_employer.canonical_id}] ({match.tier})")
        print(f"      Education: {edu.level.value} ({edu.confidence})"
              f"{f' — matched: {edu.matched_text}' if edu.matched_text else ''}")
        print(f"      Resumes to generate: {resume_count}")
        if job.salary:
            print(f"      Salary: {job.salary}")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Jobs scraped:         {len(jobs)}")
    print(f"  Unique employers:     {len(registry.employers)}")
    print(f"  Duplicates caught:    {len(jobs) - len(registry.employers)}")
    print(f"  Review queue:         {len(registry.review_queue)}")

    output = [asdict(j) for j in jobs]
    with open("scraped_jobs.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Raw data saved to scraped_jobs.json")


if __name__ == "__main__":
    run_scraper_demo()
