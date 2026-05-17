"""
FNOL Agent - First Notice of Loss Processing System
Uses regex patterns to extract fields — NO API KEY REQUIRED
"""

import json
import re
import argparse
from pathlib import Path
from typing import Optional

# ── Routing thresholds & keywords ──────────────────────────────────────────
FAST_TRACK_THRESHOLD = 25_000
FRAUD_KEYWORDS = ["fraud", "inconsistent", "staged", "suspicious", "fabricated"]
MANDATORY_FIELDS = [
    "policy_number", "policyholder_name", "effective_date_start", "effective_date_end",
    "incident_date", "incident_time", "incident_location", "incident_description",
    "claimant_name", "claimant_contact",
    "asset_type", "estimated_damage",
    "claim_type", "initial_estimate"
]

# ── Regex patterns for each field ──────────────────────────────────────────
FIELD_PATTERNS = {

    "policy_number": [
        r"Policy\s*Number\s*[:\-]\s*(?P<val>POL[\w\-]+)",
        r"Policy\s*(?:No|#|Num)\s*[:\-]\s*(?P<val>[\w\-]+)",
    ],

    "policyholder_name": [
        r"Policyholder\s*Name\s*[:\-]\s*(?P<val>[A-Za-z][A-Za-z\s]+?)(?:\n|$)",
        r"Insured\s*Name\s*[:\-]\s*(?P<val>[A-Za-z][A-Za-z\s]+?)(?:\n|$)",
    ],

    "effective_date_start": [
        r"Effective\s*Date\s*\(Start\)\s*[:\-]\s*(?P<val>\d{1,2}[\-\/]\w+[\-\/]\d{2,4})",
        r"Policy\s*Start\s*Date\s*[:\-]\s*(?P<val>\d{1,2}[\-\/]\w+[\-\/]\d{2,4})",
        # No open fallback - blank field should stay blank
    ],

    "effective_date_end": [
        r"Effective\s*Date\s*\(End\)\s*[:\-]\s*(?P<val>\d{1,2}[\-\/]\w+[\-\/]\d{2,4})",
        r"Policy\s*End\s*Date\s*[:\-]\s*(?P<val>\d{1,2}[\-\/]\w+[\-\/]\d{2,4})",
        # No open fallback - blank field should stay blank
    ],

    "incident_date": [
        r"Date\s*of\s*Incident\s*[:\-]\s*(?P<val>\d{1,2}[\-\/]\w+[\-\/]\d{2,4})",
        r"Incident\s*Date\s*[:\-]\s*(?P<val>\d{1,2}[\-\/]\w+[\-\/]\d{2,4})",
    ],

    "incident_time": [
        r"Time\s*of\s*Incident\s*[:\-]\s*(?P<val>\d{1,2}:\d{2}(?:\s*[APap][Mm])?)",
        r"Incident\s*Time\s*[:\-]\s*(?P<val>\d{1,2}:\d{2}(?:\s*[APap][Mm])?)",
        r"Time\s*[:\-]\s*(?P<val>\d{1,2}:\d{2}(?:\s*[APap][Mm])?)",
    ],

    "incident_location": [
        r"Location\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Place\s*of\s*Incident\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "incident_description": [
        r"Description\s*[:\-]\s*(?P<val>.+?)(?=\n[A-Z][A-Z ]{3,}\n|\Z)",
        r"Narrative\s*[:\-]\s*(?P<val>.+?)(?=\n[A-Z][A-Z ]{3,}\n|\Z)",
    ],

    "claimant_name": [
        r"Claimant\s*[:\-]\s*(?P<val>[A-Za-z][A-Za-z\s]+?)(?:\n|$)",
        r"Claimant\s*Name\s*[:\-]\s*(?P<val>[A-Za-z][A-Za-z\s]+?)(?:\n|$)",
    ],

    "third_parties": [
        r"Third\s*Party\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Third\s*Parties\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "claimant_contact": [
        r"Contact\s*Details?\s*\(Claimant\)\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Claimant\s*Contact\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "third_party_contact": [
        r"Contact\s*Details?\s*\(Third\s*Party\)\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Third\s*Party\s*Contact\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "asset_type": [
        r"Asset\s*Type\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Vehicle\s*Type\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "asset_id": [
        r"Asset\s*ID\s*(?:\([^)]+\))?\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Vehicle\s*Reg(?:istration)?\s*(?:\([^)]+\))?\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Property\s*Ref(?:erence)?\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "estimated_damage": [
        r"Estimated\s*Damage\s*[:\-]\s*[^\d]*(?P<val>[\d,]+(?:\.\d+)?)",
        r"Estimated\s*Loss\s*[:\-]\s*[^\d]*(?P<val>[\d,]+(?:\.\d+)?)",
        r"Damage\s*Estimate\s*[:\-]\s*[^\d]*(?P<val>[\d,]+(?:\.\d+)?)",
    ],

    "claim_type": [
        r"Claim\s*Type\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Type\s*of\s*Claim\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "attachments": [
        r"Attachments?\s*[:\-]\s*(?P<val>[^\n]+)",
        r"Documents?\s*Attached\s*[:\-]\s*(?P<val>[^\n]+)",
    ],

    "initial_estimate": [
        r"Initial\s*Estimate\s*[:\-]\s*[^\d]*(?P<val>[\d,]+(?:\.\d+)?)",
        r"Preliminary\s*Estimate\s*[:\-]\s*[^\d]*(?P<val>[\d,]+(?:\.\d+)?)",
    ],
}


def _is_section_header(text: str) -> bool:
    """Return True if the string looks like a section header rather than a real value."""
    # All-caps line with optional spaces (e.g. "INCIDENT INFORMATION")
    return bool(re.match(r'^[A-Z][A-Z\s\-]{4,}$', text.strip()))

def extract_fields(fnol_text: str) -> dict:
    """Extract all fields using regex. Returns dict with empty string for missing fields."""
    text = re.sub(r'\r\n', '\n', fnol_text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    extracted = {}
    for field, patterns in FIELD_PATTERNS.items():
        value = ""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                raw = match.group("val").strip()
                # Take only the first line to avoid bleeding into adjacent sections
                raw = raw.split('\n')[0].strip()
                # Skip if it looks like a section header (false match on blank field)
                if _is_section_header(raw):
                    continue
                raw = re.sub(r'\s+', ' ', raw).strip(" :-–")
                if field in ("estimated_damage", "initial_estimate"):
                    raw = raw.replace(",", "")
                skip_values = {"n/a", "na", "-", "—", "–", "none", ""}
                if raw.lower() not in skip_values:
                    value = raw
                    break
        extracted[field] = value

    return extracted


def identify_missing_fields(extracted: dict) -> list:
    """Return list of mandatory fields that are blank."""
    return [f for f in MANDATORY_FIELDS if not extracted.get(f, "").strip()]


def get_damage_amount(extracted: dict) -> Optional[float]:
    """Parse estimated_damage to float."""
    raw = extracted.get("estimated_damage", "")
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(raw))
    try:
        return float(cleaned)
    except ValueError:
        return None


def determine_route(extracted: dict, missing_fields: list) -> dict:
    """
    Apply routing rules in priority order — pure logic, zero dependencies.

    Priority:
      1. Fraud keywords in description  → Investigation Flag
      2. Claim type contains 'injury'   → Specialist Queue
      3. Any mandatory field missing    → Manual Review
      4. Damage < threshold             → Fast-track
      5. Else                           → Standard Processing
    """
    description = extracted.get("incident_description", "").lower()
    claim_type  = extracted.get("claim_type", "").lower()
    damage      = get_damage_amount(extracted)

    # Rule 1
    found = [kw for kw in FRAUD_KEYWORDS if kw in description]
    if found:
        return {
            "recommendedRoute": "Investigation Flag",
            "reasoning": (
                f"Incident description contains suspicious keyword(s): "
                f"{', '.join(repr(k) for k in found)}. "
                "Claim flagged for investigation before further processing."
            )
        }

    # Rule 2
    if "injury" in claim_type:
        return {
            "recommendedRoute": "Specialist Queue",
            "reasoning": (
                f"Claim type is '{extracted.get('claim_type')}', which requires specialist "
                "handling. Routed to the injury/medical specialist queue."
            )
        }

    # Rule 3
    if missing_fields:
        friendly = [f.replace("_", " ") for f in missing_fields]
        return {
            "recommendedRoute": "Manual Review",
            "reasoning": (
                f"{len(missing_fields)} mandatory field(s) are missing: "
                f"{', '.join(friendly)}. Manual review required to complete the record."
            )
        }

    # Rule 4
    if damage is not None and damage < FAST_TRACK_THRESHOLD:
        return {
            "recommendedRoute": "Fast-track",
            "reasoning": (
                f"All mandatory fields present and estimated damage "
                f"(Rs.{damage:,.0f}) is below the Rs.{FAST_TRACK_THRESHOLD:,} threshold. "
                "Approved for expedited processing."
            )
        }

    # Rule 5
    damage_str = f"Rs.{damage:,.0f}" if damage else "unknown"
    return {
        "recommendedRoute": "Standard Processing",
        "reasoning": (
            f"All mandatory fields present, no fraud indicators, claim type is not injury, "
            f"and estimated damage ({damage_str}) exceeds the fast-track threshold."
        )
    }


def process_fnol(fnol_text: str, source_file: str = "unknown") -> dict:
    """Full pipeline: extract -> validate -> route -> return structured output."""
    print(f"\n{'='*60}")
    print(f"  Processing: {source_file}")
    print(f"{'='*60}")

    print("  [1/3] Extracting fields via regex patterns...")
    extracted = extract_fields(fnol_text)

    print("  [2/3] Checking for missing mandatory fields...")
    missing = identify_missing_fields(extracted)

    print("  [3/3] Applying routing rules...")
    routing = determine_route(extracted, missing)

    return {
        "source_file": source_file,
        "extractedFields": extracted,
        "missingFields": missing,
        "recommendedRoute": routing["recommendedRoute"],
        "reasoning": routing["reasoning"],
    }


def print_result(result: dict):
    print(f"\n{'─'*60}")
    print(f"  RESULT: {result['source_file']}")
    print(f"{'─'*60}")

    print("\n  EXTRACTED FIELDS:")
    for k, v in result["extractedFields"].items():
        if v:
            print(f"     {k:30s}: {v}")

    if result["missingFields"]:
        print(f"\n  WARNING - MISSING FIELDS ({len(result['missingFields'])}):")
        for f in result["missingFields"]:
            print(f"     - {f}")
    else:
        print("\n  OK: All mandatory fields present")

    icons = {
        "Fast-track": "FAST-TRACK",
        "Manual Review": "MANUAL REVIEW",
        "Investigation Flag": "INVESTIGATION FLAG",
        "Specialist Queue": "SPECIALIST QUEUE",
        "Standard Processing": "STANDARD",
    }
    print(f"\n  ROUTE    : {result['recommendedRoute']}")
    print(f"  REASONING: {result['reasoning']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="FNOL Agent - regex-based claims processor (no API key needed)"
    )
    parser.add_argument("input", nargs="?",
        help="Path to FNOL .txt file (omit to process all sample FNOLs)")
    parser.add_argument("--output-dir", default="./output",
        help="Directory to save JSON results (default: ./output)")
    parser.add_argument("--no-save", action="store_true",
        help="Skip writing JSON output files")
    args = parser.parse_args()

    if args.input:
        files = [Path(args.input)]
    else:
        sample_dir = Path(__file__).parent / "sample_fnols"
        files = sorted(sample_dir.glob("*.txt"))
        if not files:
            print("No .txt FNOL files found in ./sample_fnols/")
            return

    print(f"\nFNOL AGENT  (regex mode - no API key needed)")
    print(f"Processing {len(files)} document(s)...\n")

    output_dir = Path(args.output_dir)
    if not args.no_save:
        output_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    for file_path in files:
        try:
            fnol_text = file_path.read_text(encoding="utf-8")
            result = process_fnol(fnol_text, source_file=file_path.name)
            print_result(result)
            all_results.append(result)

            if not args.no_save:
                out_file = output_dir / f"{file_path.stem}_result.json"
                out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"  Saved -> {out_file}")

        except Exception as e:
            print(f"\n  ERROR processing {file_path.name}: {e}")

    if not args.no_save and all_results:
        combined = output_dir / "all_results.json"
        combined.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nCombined results -> {combined}")

    if all_results:
        print(f"\n{'='*60}  SUMMARY")
        routes: dict = {}
        for r in all_results:
            rt = r["recommendedRoute"]
            routes[rt] = routes.get(rt, 0) + 1
        for route, count in sorted(routes.items()):
            print(f"  {route:25s}: {count} claim(s)")
        print()


if __name__ == "__main__":
    main()
