"""
Smoke test for ProjectDatabaseManager.
Run from the ISP root directory:

    python shared/test_db_manager.py

Make sure your .env file is populated with valid Supabase credentials
and the 'interview-assets' bucket exists (can be public or private).
"""

import sys
import os
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.db_manager import ProjectDatabaseManager

def run_smoke_test():
    print("=" * 55)
    print("  ProjectDatabaseManager Smoke Test")
    print("=" * 55)

    db = ProjectDatabaseManager()

    # 1. Create session
    print("\n[1] Creating session…")
    session_id = db.create_session({
        "name": "Test Candidate",
        "email": "test@example.com",
        "phone": "9999999999",
        "age": 25,
        "job_profile": "Software Engineer",
    })
    print(f"    ✓ Session created: {session_id}")

    # 2. Upload a tiny dummy image
    print("\n[2] Uploading dummy image…")
    dummy_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # Minimal JPEG stub
    url = db.upload_image(session_id, dummy_jpeg)
    print(f"    ✓ Image URL: {url}")

    # 3. Fetch session and verify
    print("\n[3] Fetching session…")
    row = db.get_session(session_id)
    assert row is not None, "Session not found after creation!"
    assert row["name"] == "Test Candidate", "Name mismatch!"
    assert row["user_image_url"] is not None, "user_image_url not set!"
    print(f"    ✓ Session fetched: name={row['name']}, image_url set={bool(row['user_image_url'])}")

    # 4. List sessions
    print("\n[4] Listing sessions…")
    sessions = db.list_sessions()
    assert len(sessions) >= 1, "Expected at least 1 session!"
    print(f"    ✓ Found {len(sessions)} session(s) in DB")

    # 5. Update OCEAN scores
    print("\n[5] Updating OCEAN scores…")
    scores = {"O": 3.2, "C": 4.1, "E": 2.8, "A": 3.9, "N": 1.5}
    db.update_ocean_score(session_id, scores)
    row2 = db.get_session(session_id)
    assert row2["ocean_score"] is not None, "ocean_score not updated!"
    print(f"    ✓ OCEAN scores saved: {row2['ocean_score']}")

    print("\n" + "=" * 55)
    print("  All smoke tests passed! ✓")
    print("=" * 55)


if __name__ == "__main__":
    run_smoke_test()
