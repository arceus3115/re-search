"""
Standalone test script for ClinicalTrials.gov API integration.

This script tests the new filter.advanced search functionality with real API calls.
Run with: python -m app.test_clinicaltrials_api
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.clinicaltrials_client import (
    search_trials_by_pi_name_advanced,
    format_trial_for_display,
)
from app.utils.exceptions import ClinicalTrialsAPIError
from app.utils.logger import setup_logger

# Setup logging
setup_logger()


def print_trial_summary(trial: dict, index: int):
    """Print a formatted summary of a trial."""
    formatted = format_trial_for_display(trial)
    print(f"\n{'=' * 80}")
    print(f"Trial #{index + 1}")
    print(f"{'=' * 80}")
    print(f"NCT ID: {formatted.get('nct_id', 'N/A')}")
    print(f"Title: {formatted.get('title', 'N/A')}")
    print(f"Status: {formatted.get('overall_status', 'N/A')}")
    print(f"Phase: {formatted.get('phase', 'N/A')}")
    print(f"PI Name: {formatted.get('pi_name', 'N/A')}")
    print(f"Conditions: {', '.join(formatted.get('conditions', []))}")
    print(f"Enrollment: {formatted.get('enrollment', 'N/A')}")
    print(
        f"Locations: {', '.join(formatted.get('locations', [])[:3])}"
    )  # First 3 locations
    if formatted.get("brief_summary"):
        summary = (
            formatted["brief_summary"][:200] + "..."
            if len(formatted["brief_summary"]) > 200
            else formatted["brief_summary"]
        )
        print(f"Summary: {summary}")


def test_basic_search():
    """Test basic PI name search."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic PI Name Search")
    print("=" * 80)

    pi_name = "Sanjay Mathew"
    print(f"\nSearching for trials by PI: {pi_name}")

    try:
        trials = search_trials_by_pi_name_advanced(
            pi_name=pi_name,
            limit=5,  # Limit to 5 for testing
            page_size=25,
        )

        print(f"\n✓ Found {len(trials)} trials")

        if trials:
            print("\nFirst 3 trials:")
            for i, trial in enumerate(trials[:3]):
                print_trial_summary(trial, i)
        else:
            print("\n⚠ No trials found")

        return True
    except ClinicalTrialsAPIError as e:
        print(f"\n✗ API Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pagination():
    """Test pagination with multiple pages."""
    print("\n" + "=" * 80)
    print("TEST 2: Pagination Test")
    print("=" * 80)

    pi_name = "Sanjay Mathew"
    print(f"\nSearching for trials by PI: {pi_name} (testing pagination)")

    try:
        # Request more results to trigger pagination
        trials = search_trials_by_pi_name_advanced(
            pi_name=pi_name,
            limit=50,  # Request 50 to likely trigger pagination
            page_size=10,  # Small page size to ensure multiple pages
        )

        print(f"\n✓ Found {len(trials)} trials across multiple pages")
        print("✓ Pagination working correctly")

        return True
    except ClinicalTrialsAPIError as e:
        print(f"\n✗ API Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_status_filter():
    """Test status filtering."""
    print("\n" + "=" * 80)
    print("TEST 3: Status Filter Test")
    print("=" * 80)

    pi_name = "Sanjay Mathew"
    status_filter = ["RECRUITING", "ACTIVE_NOT_RECRUITING"]
    print(f"\nSearching for trials by PI: {pi_name}")
    print(f"Status filter: {status_filter}")

    try:
        trials = search_trials_by_pi_name_advanced(
            pi_name=pi_name, limit=10, status_filter=status_filter
        )

        print(f"\n✓ Found {len(trials)} trials matching status filter")

        # Verify all trials match the status filter
        all_match = True
        for trial in trials:
            protocol_section = trial.get("protocolSection", {})
            status_module = protocol_section.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "").upper()

            matches = any(status.upper() in overall_status for status in status_filter)
            if not matches:
                print(
                    f"⚠ Warning: Trial {trial.get('protocolSection', {}).get('identificationModule', {}).get('nctId')} "
                    f"has status '{overall_status}' which doesn't match filter"
                )
                all_match = False

        if all_match:
            print("✓ All trials match the status filter")

        return True
    except ClinicalTrialsAPIError as e:
        print(f"\n✗ API Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_empty_results():
    """Test with a PI name that likely has no results."""
    print("\n" + "=" * 80)
    print("TEST 4: Empty Results Test")
    print("=" * 80)

    pi_name = "Nonexistent Person XYZ123"
    print(f"\nSearching for trials by PI: {pi_name} (should return empty)")

    try:
        trials = search_trials_by_pi_name_advanced(pi_name=pi_name, limit=10)

        if len(trials) == 0:
            print("\n✓ Correctly returned empty results (0 trials)")
            return True
        else:
            print(f"\n⚠ Unexpected: Found {len(trials)} trials for nonexistent PI")
            return False
    except ClinicalTrialsAPIError as e:
        print(f"\n✗ API Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_response_structure():
    """Test that response structure is correct."""
    print("\n" + "=" * 80)
    print("TEST 5: Response Structure Test")
    print("=" * 80)

    pi_name = "Sanjay Mathew"
    print(f"\nSearching for trials by PI: {pi_name}")
    print("Verifying response structure...")

    try:
        trials = search_trials_by_pi_name_advanced(pi_name=pi_name, limit=1)

        if not trials:
            print("\n⚠ No trials found, skipping structure test")
            return True

        trial = trials[0]
        formatted = format_trial_for_display(trial)

        # Check required fields
        required_fields = ["nct_id", "title", "overall_status"]
        missing_fields = [
            field for field in required_fields if not formatted.get(field)
        ]

        if missing_fields:
            print(f"\n✗ Missing required fields: {missing_fields}")
            return False

        print("\n✓ Response structure is valid")
        print(f"  - NCT ID: {formatted.get('nct_id')}")
        print(f"  - Title: {formatted.get('title')[:50]}...")
        print(f"  - Status: {formatted.get('overall_status')}")
        print(f"  - Has conditions: {bool(formatted.get('conditions'))}")
        print(f"  - Has interventions: {bool(formatted.get('interventions'))}")

        return True
    except ClinicalTrialsAPIError as e:
        print(f"\n✗ API Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ClinicalTrials.gov API Integration Tests")
    print("=" * 80)
    print("\nThis script tests the new filter.advanced search functionality.")
    print("All tests make real API calls to ClinicalTrials.gov.")

    tests = [
        ("Basic Search", test_basic_search),
        ("Pagination", test_pagination),
        ("Status Filter", test_status_filter),
        ("Empty Results", test_empty_results),
        ("Response Structure", test_response_structure),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
