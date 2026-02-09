"""
Evaluation Test Cases (Robust + Document-Coverage)
Checks grounding, citations, no placeholders, and honest NOT FOUND behavior.
"""

import re
import sys
import os

TEST_CASES = [
    # project_report.md
    {
        "id": 1,
        "type": "extraction",
        "input": "List the top 3 key risks mentioned in the project documents. For each risk, include a short explanation and citation.",
        "required_sources": ["project_report.md"],
        "min_items": 3,
    },

    # weekly_update.md
    {
        "id": 2,
        "type": "extraction",
        "input": "From the weekly update, list the concrete work completed this week and the planned work for next week as bullets with citations.",
        "required_sources": ["weekly_update.md"],
        "min_items": 3,
    },

    # meeting_notes.md
    {
        "id": 3,
        "type": "extraction",
        "input": "Extract the action items from the meeting notes with owner and due date. Use a numbered list and cite sources.",
        "required_sources": ["meeting_notes.md"],
        "min_items": 3,
    },

    # q1_roadmap.md
    {
        "id": 4,
        "type": "extraction",
        "input": "From the Q1 roadmap, list milestones and any available dates/status. If a field is not in the docs, explicitly say NOT FOUND IN SOURCES for that field (do not guess). Cite sources.",
        "required_sources": ["q1_roadmap.md"],
        "min_items": 3,
    },

    # technical_specs.md
    {
        "id": 5,
        "type": "summary",
        "input": "Summarize the system architecture (frontend, backend, infrastructure) and the key performance + security requirements with citations.",
        "required_sources": ["technical_specs.md"],
        "min_citations": 2,
    },

    # client_feedback.md
    {
        "id": 6,
        "type": "analysis",
        "input": "From client feedback, list the top 3 improvement requests and any explicitly stated success metrics (numbers). If metrics are not present, say NOT FOUND IN SOURCES. Cite sources.",
        "required_sources": ["client_feedback.md"],
        "min_items": 3,
    },

    # competitor_analysis.md
    {
        "id": 7,
        "type": "analysis",
        "input": "Using the competitor analysis, compare us vs competitors and provide 3 recommended strategy points with citations.",
        "required_sources": ["competitor_analysis.md"],
        "min_items": 3,
    },

    # Not found behavior (should not invent)
    {
        "id": 8,
        "type": "not_found",
        "input": "What is the CEO's favorite color? Answer ONLY if present in the provided documents; otherwise say NOT FOUND IN SOURCES.",
        "required_sources": [],
        "must_contain_any": ["not found", "not mentioned", "not available", "not present"],
        "must_not_contain_any": ["blue", "green", "red", "purple", "yellow"],
    },
    # Cross-document: email generation from weekly update
     {
        "id": 9,
        "type": "analysis",
        "input": "Draft a brief client update email summarizing this week's progress and next week's plans. Use only information from the documents and cite sources.",
        "required_sources": ["weekly_update.md"],
        "min_citations": 2,
    },

    # Cross-document: compare budget info across documents
    {
        "id": 10,
        "type": "analysis",
        "input": "What is the current budget status of the project? Include total budget, amount spent, and any concerns. Cite all sources.",
        "required_sources": ["project_report.md"],
        "min_citations": 1,
    },
]

# ---------- Validation helpers ----------

BRACKETS_RE = re.compile(r"\[[^\]]+\]")
SOURCE_CITATION_RE = re.compile(r"\[Source:\s*[^\]]+\]", re.IGNORECASE)

def has_placeholders(text: str) -> bool:
    """Any [...] that is NOT [Source: ...] is a placeholder/template."""
    brackets = BRACKETS_RE.findall(text or "")
    for b in brackets:
        if not SOURCE_CITATION_RE.match(b):
            return True
    return False

def contains_required_sources(text: str, required_sources: list[str]) -> bool:
    low = (text or "").lower()
    return all(src.lower() in low for src in required_sources)

def count_citations(text: str) -> int:
    low = (text or "")
    return len(re.findall(r"\[Source:\s*[^\]]+\]", low, flags=re.IGNORECASE))

def count_list_items(text: str) -> int:
    if not text:
        return 0
    bullets = text.count("\n- ")
    numbered = len(re.findall(r"\n\d+\.", text))
    return bullets + numbered

def contains_any(text: str, phrases: list[str]) -> bool:
    low = (text or "").lower()
    return any(p.lower() in low for p in phrases)

def contains_none(text: str, phrases: list[str]) -> bool:
    low = (text or "").lower()
    return all(p.lower() not in low for p in phrases)

# ---------- Runner ----------

def run_evaluation():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.workflow import run_assistant

    results = []

    for test in TEST_CASES:
        print(f"\n{'='*70}")
        print(f"Test {test['id']}: {test['type'].upper()}")
        print(f"Input: {test['input']}")
        print(f"{'='*70}")

        try:
            result = run_assistant(test["input"])
            output = result.get("final_output", result.get("draft", "")) or ""

            print("\nFinal Output (truncated):")
            print(output[:700] + ("..." if len(output) > 700 else ""))

            checks = {}

            # must not have placeholders
            checks["no_placeholders"] = not has_placeholders(output)

            # required sources
            checks["required_sources_present"] = contains_required_sources(output, test.get("required_sources", []))

            # list items requirement (if defined)
            if "min_items" in test:
                checks["min_items"] = count_list_items(output) >= test["min_items"]
            else:
                checks["min_items"] = True

            # citation count requirement (if defined)
            if "min_citations" in test:
                checks["min_citations"] = count_citations(output) >= test["min_citations"]
            else:
                # for everything except not_found, require at least one citation
                if test["type"] != "not_found":
                    checks["min_citations"] = count_citations(output) >= 1
                else:
                    checks["min_citations"] = True

            # must contain any phrases (if defined)
            if "must_contain_any" in test:
                checks["must_contain_any"] = contains_any(output, test["must_contain_any"])
            else:
                checks["must_contain_any"] = True

            # must NOT contain any phrases (if defined)
            if "must_not_contain_any" in test:
                checks["must_not_contain_any"] = contains_none(output, test["must_not_contain_any"])
            else:
                checks["must_not_contain_any"] = True

            objective_pass = all(checks.values())

            print("\nObjective Checks:")
            for k, v in checks.items():
                print(f"  - {k}: {'PASS' if v else 'FAIL'}")

            verifier_pass = bool(result.get("verification_passed"))

            print("\nSystem Verifier:", "PASSED" if verifier_pass else "ISSUES FOUND")
            print("Overall:", "PASS" if (objective_pass and verifier_pass) else "FAIL")

            results.append({
                "test_id": test["id"],
                "type": test["type"],
                "objective_pass": objective_pass,
                "verifier_pass": verifier_pass,
                "checks": checks,
            })

        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append({
                "test_id": test["id"],
                "type": test["type"],
                "objective_pass": False,
                "verifier_pass": False,
                "error": str(e),
            })

    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)

    total = len(results)
    objective_ok = sum(1 for r in results if r.get("objective_pass"))
    verifier_ok = sum(1 for r in results if r.get("verifier_pass"))
    both_ok = sum(1 for r in results if r.get("objective_pass") and r.get("verifier_pass"))

    print(f"Total tests: {total}")
    print(f"Objective checks passed: {objective_ok}/{total}")
    print(f"Verifier passed: {verifier_ok}/{total}")
    print(f"Both passed: {both_ok}/{total}")

    return results


if __name__ == "__main__":
    run_evaluation()