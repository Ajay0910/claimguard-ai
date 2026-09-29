#!/usr/bin/env python3
"""
E2E Test Runner for ClaimGuard AI Hardening.
Executes all 4 tiers of E2E requirement-driven tests and prints a detailed test report.
Usage:
    python backend/tests/e2e/run_tests.py
    pytest backend/tests/e2e/ -v
"""

import sys
import os
import pytest

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    backend_dir = os.path.join(repo_root, "backend")
    e2e_dir = os.path.join(backend_dir, "tests", "e2e")
    
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
        
    print("=" * 70)
    print("ClaimGuard AI Hardening: 4-Tier E2E Test Suite Execution")
    print(f"Target Directory: {e2e_dir}")
    print("=" * 70)
    
    args = [
        e2e_dir,
        "-v",
        "--tb=short"
    ]
    exit_code = pytest.main(args)
    print("=" * 70)
    if exit_code == 0:
        print("[SUCCESS] All E2E tests passed cleanly.")
    else:
        print(f"[FAILURE] Test suite exited with code: {exit_code}")
    print("=" * 70)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
