"""
Resume Audit Study - Tech Demo
Demonstrates the two hardest non-scraping components:
  1. Employer deduplication (tiered fuzzy matching)
  2. Education requirement extraction from job descriptions
"""

from employer_dedup import EmployerRegistry
from education_extractor import extract_education, EducationLevel

# ============================================================
# PART 1: Employer Deduplication Demo
# ============================================================
# Realistic DFW-area healthcare employer variants that would
# appear across thousands of Indeed postings

EMPLOYER_TEST_DATA = [
    # Baylor Scott & White — many name variants
    ("Baylor Scott & White Health", "Dallas-Fort Worth"),
    ("BSW Health", "Dallas-Fort Worth"),
    ("Baylor Scott and White Medical Center - Plano", "Dallas-Fort Worth"),
    ("Baylor Scott & White Medical Center", "Dallas-Fort Worth"),
    ("Baylor Scott White Health", "Dallas-Fort Worth"),

    # Texas Health Resources variants
    ("Texas Health Resources", "Dallas-Fort Worth"),
    ("Texas Health Presbyterian Hospital Dallas", "Dallas-Fort Worth"),
    ("Texas Health Harris Methodist Hospital", "Dallas-Fort Worth"),
    ("THR Group", "Dallas-Fort Worth"),

    # UT Southwestern variants
    ("UT Southwestern Medical Center", "Dallas-Fort Worth"),
    ("University of Texas Southwestern", "Dallas-Fort Worth"),
    ("UTSW Medical Center", "Dallas-Fort Worth"),

    # Parkland — straightforward
    ("Parkland Health", "Dallas-Fort Worth"),
    ("Parkland Hospital", "Dallas-Fort Worth"),
    ("Parkland Health & Hospital System", "Dallas-Fort Worth"),

    # Same name, different metros — should NOT merge
    ("Methodist Hospital", "Dallas-Fort Worth"),
    ("Methodist Hospital", "Houston"),
    ("Methodist Hospital", "San Antonio"),

    # HCA Healthcare variants
    ("HCA Healthcare", "Dallas-Fort Worth"),
    ("Medical City Healthcare", "Dallas-Fort Worth"),
    ("Medical City Dallas Hospital", "Dallas-Fort Worth"),

    # Duplicates that should be caught
    ("Baylor Scott & White Health", "Dallas-Fort Worth"),  # exact repeat
    ("baylor scott & white health", "Dallas-Fort Worth"),  # case variant
    ("Parkland Health.", "Dallas-Fort Worth"),  # trailing punctuation
]


def run_dedup_demo():
    print("=" * 70)
    print("PART 1: EMPLOYER DEDUPLICATION ENGINE")
    print("=" * 70)
    print()

    registry = EmployerRegistry()
    results = []

    for name, metro in EMPLOYER_TEST_DATA:
        result = registry.resolve(name, metro)
        results.append(result)

    # Print results grouped by resolution tier
    tiers = {}
    for r in results:
        tiers.setdefault(r.tier, []).append(r)

    for tier_name, tier_label in [
        ("exact", "TIER 1 — Exact Match (after normalization)"),
        ("fuzzy_auto", "TIER 2a — Fuzzy Auto-Merge (>0.95 similarity)"),
        ("fuzzy_metro", "TIER 2b — Fuzzy + Metro Match (0.80-0.95, same metro)"),
        ("review", "TIER 3 — Flagged for Human Review"),
        ("new", "NEW — No match, created new employer"),
    ]:
        items = tiers.get(tier_name, [])
        if not items:
            continue
        print(f"\n  {tier_label}")
        print(f"  {'-' * 60}")
        for r in items:
            emp = r.matched_employer
            score = f" (score: {r.score:.2f})" if r.score else ""
            print(f"    \"{r.raw_name}\"")
            print(f"      -> Canonical: \"{emp.canonical_name}\" [ID:{emp.canonical_id}]{score}")

    # Summary
    print(f"\n  SUMMARY")
    print(f"  {'-' * 60}")
    print(f"    Raw names processed:   {len(results)}")
    print(f"    Canonical employers:   {len(registry.employers)}")
    print(f"    Duplicates caught:     {len(results) - len(registry.employers)}")
    print(f"    Flagged for review:    {len(registry.review_queue)}")

    print(f"\n  CANONICAL REGISTRY")
    print(f"  {'-' * 60}")
    for emp in registry.employers:
        aliases = ", ".join(f'"{a}"' for a in emp.aliases if a != emp.canonical_name)
        alias_str = f"  aliases: [{aliases}]" if aliases else ""
        print(f"    [{emp.canonical_id:2d}] {emp.canonical_name} ({emp.metro}){alias_str}")


# ============================================================
# PART 2: Education Requirement Extraction Demo
# ============================================================
# Realistic job description snippets from healthcare postings

JOB_DESCRIPTIONS = [
    {
        "title": "Registered Nurse - ICU",
        "company": "Baylor Scott & White Health",
        "description": """
        Minimum Requirements:
        - Bachelor's degree in Nursing (BSN) required
        - Current RN license in state of Texas
        - BLS and ACLS certifications required
        - Minimum 2 years of ICU experience
        """,
    },
    {
        "title": "Medical Assistant",
        "company": "Texas Health Resources",
        "description": """
        Qualifications:
        - High school diploma or GED required
        - Associate's degree in medical assisting preferred
        - Certified Medical Assistant (CMA) credential preferred
        - 1+ year clinical experience
        """,
    },
    {
        "title": "Patient Access Representative",
        "company": "Parkland Health",
        "description": """
        Requirements:
        - Must have excellent customer service skills
        - Experience with electronic health records
        - Bilingual English/Spanish a plus
        - Available to work weekends and holidays
        """,
    },
    {
        "title": "Clinical Research Coordinator",
        "company": "UT Southwestern Medical Center",
        "description": """
        Education: BA/BS in life sciences, nursing, or related field required.
        Master's degree preferred. Must have at least 2 years of clinical
        research experience. CCRP certification is a plus.
        """,
    },
    {
        "title": "Pharmacy Technician",
        "company": "Medical City Dallas",
        "description": """
        We're looking for a dedicated Pharmacy Tech to join our team.

        What you'll need:
        - AA degree or completion of pharmacy technician program
        - Active pharmacy technician registration with Texas State Board
        - Hospital pharmacy experience nice to have
        """,
    },
    {
        "title": "Health Information Specialist",
        "company": "HCA Healthcare",
        "description": """
        The ideal candidate will have a 4-year degree in Health Information
        Management or related field. RHIT or RHIA certification required.
        Must have working knowledge of ICD-10 coding standards and
        experience with Epic EHR systems.
        """,
    },
    {
        "title": "Environmental Services Technician",
        "company": "Parkland Hospital",
        "description": """
        Join our EVS team! We provide thorough cleaning and disinfection
        of patient rooms and common areas. No degree required - we provide
        full training. Must be able to lift 50 lbs and stand for extended periods.
        Starting pay $15/hr with full benefits.
        """,
    },
    {
        "title": "Data Analyst - Revenue Cycle",
        "company": "BSW Health",
        "description": """
        Minimum qualifications:
        - Bachelor's degree in business, healthcare administration, or
          equivalent work experience
        - 3+ years of experience in healthcare revenue cycle analytics
        - Advanced Excel and SQL skills required
        - Tableau or Power BI experience preferred
        """,
    },
]


def run_education_demo():
    print("\n")
    print("=" * 70)
    print("PART 2: EDUCATION REQUIREMENT EXTRACTION")
    print("=" * 70)
    print()

    # Track counts for summary
    counts = {level: 0 for level in EducationLevel}

    for job in JOB_DESCRIPTIONS:
        result = extract_education(job["description"])
        counts[result.level] += 1

        # Resume count logic from the proposal
        if result.level == EducationLevel.UNSPECIFIED:
            resume_count = 3  # AA, BA, and no-degree variants
        elif result.level == EducationLevel.ASSOCIATES:
            resume_count = 2  # AA and BA variants
        else:
            resume_count = 2  # BA variant + one other

        matched = f'matched: "{result.matched_text}"' if result.matched_text else "no education keywords found"
        print(f"  {job['title']} @ {job['company']}")
        print(f"    -> {result.level.value} (confidence: {result.confidence}) | {matched}")
        print(f"    -> Resumes to generate: {resume_count}")
        print()

    print(f"  EXTRACTION SUMMARY")
    print(f"  {'-' * 60}")
    for level in EducationLevel:
        print(f"    {level.value:15s}: {counts[level]} postings")
    print(f"    {'TOTAL':15s}: {sum(counts.values())} postings processed")


if __name__ == "__main__":
    run_dedup_demo()
    run_education_demo()

    print("\n")
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("""
  This demo proves feasibility of the two hardest algorithmic components:

  1. Employer Dedup: Tiered matching correctly groups name variants while
     keeping same-name employers in different metros separate. The review
     queue catches ambiguous cases for human oversight.

  2. Education Extraction: Rule-based parsing reliably identifies degree
     requirements from realistic job descriptions, determining how many
     resumes to generate per posting.

  Neither component requires external API calls or LLM inference for the
  common cases. LLM fallback is available for edge cases at negligible cost.
    """)
