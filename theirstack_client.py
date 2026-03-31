"""
TheirStack Job Data API Client
Resume Audit Study

Fetches job postings from TheirStack's API, which aggregates Indeed and
325k+ other sources. Returns structured data including full descriptions.

API docs: https://theirstack.com/en/docs/api-reference/jobs/search_jobs_v1
Free tier: 200 credits/month (1 credit per job returned)
Paid: $59/month for production volume
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from urllib.request import Request, urlopen
from urllib.error import HTTPError


API_URL = "https://api.theirstack.com/v1/jobs/search"


@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    description: str
    source_url: str | None
    date_posted: str | None
    salary: str | None
    remote: bool
    theirstack_id: int | None


def fetch_jobs(
    job_titles: list[str],
    location_pattern: str,
    country_code: str = "US",
    max_age_days: int = 7,
    limit: int = 25,
    source_domain: str | None = None,
    api_key: str | None = None,
) -> list[JobPosting]:
    """
    Fetch job postings from TheirStack API.

    Args:
        job_titles: List of job title patterns (e.g., ["registered nurse", "RN"])
        location_pattern: Regex pattern for location (e.g., "Dallas|Fort Worth|Plano|Frisco")
        country_code: ISO country code (default: "US")
        max_age_days: Max posting age in days
        limit: Max results to return (1 credit per result)
        source_domain: Filter to specific source (e.g., "indeed.com")
        api_key: TheirStack API key (or set THEIRSTACK_API_KEY env var)
    """
    key = api_key or os.environ.get("THEIRSTACK_API_KEY")
    if not key:
        raise ValueError(
            "No API key provided. Set THEIRSTACK_API_KEY env var or pass api_key parameter.\n"
            "Get a free key (200 credits/mo) at https://theirstack.com"
        )

    body: dict = {
        "job_title_or": job_titles,
        "job_country_code_or": [country_code],
        "job_location_pattern_or": [location_pattern],
        "posted_at_max_age_days": max_age_days,
        "limit": limit,
    }

    if source_domain:
        body["url_domain_or"] = [source_domain]

    payload = json.dumps(body).encode("utf-8")

    req = Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"TheirStack API error {e.code}: {error_body}") from e

    jobs = []
    for item in data.get("data", []):
        jobs.append(JobPosting(
            title=item.get("job_title", "Unknown"),
            company=item.get("company", "Unknown"),
            location=item.get("location", "Unknown"),
            description=item.get("description", ""),
            source_url=item.get("url"),
            date_posted=item.get("date_posted"),
            salary=item.get("salary_string"),
            remote=item.get("remote", False),
            theirstack_id=item.get("id"),
        ))

    total = data.get("metadata", {}).get("total_results", "?")
    print(f"  API returned {len(jobs)} jobs (total available: {total})")

    return jobs


def run_pipeline_demo(api_key: str | None = None):
    """Full pipeline: TheirStack API -> Dedup -> Education Extraction."""
    from employer_dedup import EmployerRegistry
    from education_extractor import extract_education

    print("=" * 70)
    print("FULL PIPELINE: TheirStack API -> Dedup -> Education Extraction")
    print("=" * 70)
    print()

    # DFW metro healthcare jobs — the study's target
    print("  Fetching DFW nursing jobs from TheirStack...")
    jobs = fetch_jobs(
        job_titles=["registered nurse", "RN", "nurse"],
        location_pattern="Dallas|Fort Worth|Plano|Frisco|Arlington|McKinney|Irving",
        max_age_days=7,
        limit=15,
        api_key=api_key,
    )

    if not jobs:
        print("  No jobs returned.")
        return

    print(f"\n  Running {len(jobs)} jobs through pipeline...\n")
    print("=" * 70)

    registry = EmployerRegistry()

    for i, job in enumerate(jobs):
        match = registry.resolve(job.company, "Dallas-Fort Worth")
        edu = extract_education(job.description)
        resume_count = 3 if edu.level.value == "unspecified" else 2

        print(f"  [{i+1}] {job.title}")
        print(f"      Company (raw):       {job.company}")
        print(f"      Canonical:           {match.matched_employer.canonical_name} "
              f"[ID:{match.matched_employer.canonical_id}] ({match.tier})")
        print(f"      Location:            {job.location}")
        matched_str = f' — matched: "{edu.matched_text}"' if edu.matched_text else ''
        print(f"      Education:           {edu.level.value} ({edu.confidence}){matched_str}")
        print(f"      Resumes to generate: {resume_count}")
        if job.salary:
            print(f"      Salary:              {job.salary}")
        if job.description:
            print(f"      Description:         {len(job.description)} chars")
        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Jobs fetched:         {len(jobs)}")
    print(f"  With descriptions:    {sum(1 for j in jobs if len(j.description) > 50)}")
    print(f"  Unique employers:     {len(registry.employers)}")
    print(f"  Duplicates caught:    {len(jobs) - len(registry.employers)}")
    print(f"  Review queue:         {len(registry.review_queue)}")

    # Save
    output = [asdict(j) for j in jobs]
    with open("scraped_jobs.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Data saved to scraped_jobs.json")


if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else None
    run_pipeline_demo(api_key=key)
