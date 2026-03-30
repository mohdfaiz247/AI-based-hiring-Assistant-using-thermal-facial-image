"""
ProjectDatabaseManager
======================
Single source of truth for all Supabase interactions.
Both interviewee_side and interviewer_side import this module.

Environment variables required (place in a .env file at the ISP root):
    SUPABASE_URL  – e.g. https://abcxyz.supabase.co
    SUPABASE_KEY  – anon or service-role key

Storage bucket:
    All files are stored in the 'interview-assets' bucket.
    Create it in the Supabase dashboard (Storage → New bucket → private).
"""

from __future__ import annotations

import os
import tempfile
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env from the ISP root (works regardless of which service runs this)
_env_path = ".env"
load_dotenv(dotenv_path=_env_path, override=False)

TABLE_NAME = "sessions"
BUCKET_NAME = "interview-assets"


class ProjectDatabaseManager:
    """
    Manages all Supabase interactions (PostgreSQL + Object Storage).

    Usage:
        db = ProjectDatabaseManager()

        # Interviewee side
        session_id = db.create_session({"name": "Alice", "email": "a@b.com", ...})
        db.upload_image(session_id, image_bytes)
        db.upload_video(session_id, Path("/tmp/interview.mp4"))

        # Interviewer side
        sessions = db.list_sessions()
        tmp_video = db.download_video(session_id)   # returns Path to temp file
        db.update_ocean_score(session_id, {"O": 3.2, "C": 4.1, ...})
        db.upload_report_pdf(session_id, pdf_bytes)
    """

    def __init__(self):
        # url = os.environ.get("SUPABASE_URL")
        # key = os.environ.get("SUPABASE_KEY")
        url="https://pykxldwtzoezgvhmuozv.supabase.co"
        key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5a3hsZHd0em9lemd2aG11b3p2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDUyOTgxOCwiZXhwIjoyMDkwMTA1ODE4fQ.5r9R5aBhkxt4MsRrB_nj8CkyIeBYEjXH1Xn076iJHQY"

        if not url or not key:
            raise EnvironmentError(
                "SUPABASE_URL and SUPABASE_KEY must be set.\n"
                "Copy .env.template to .env and fill in your credentials."
            )

        self.client: Client = create_client(url, key)
        self._active_session_id: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Session lifecycle                                                   #
    # ------------------------------------------------------------------ #

    def create_session(self, data: Dict[str, Any]) -> str:
        """
        Insert a new row into the sessions table.

        Args:
            data: Dict with any subset of the columns:
                  name, mobile, age, email, job_profile

        Returns:
            The auto-generated UUID of the new session row.
        """
        # Map interviewee registration keys → DB column names
        row = {
            "name":        data.get("name"),
            "mobile":      data.get("phone") or data.get("mobile"),
            "age":         data.get("age"),
            "email":       data.get("email"),
            "job_profile": data.get("job_profile"),
        }
        # Drop None values so DB defaults apply
        row = {k: v for k, v in row.items() if v is not None}

        try:
            response = (
                self.client.table(TABLE_NAME)
                .insert(row)
                .execute()
            )
            session_id: str = response.data[0]["id"]
            self._active_session_id = session_id
            print(f"[DB] Session created: {session_id}")
            return session_id
        except Exception as e:
            raise RuntimeError(f"[DB] Failed to create session: {e}") from e

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single session row by UUID.

        Returns:
            Dict of column → value, or None if not found.
        """
        try:
            response = (
                self.client.table(TABLE_NAME)
                .select("*")
                .eq("id", session_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"[DB] Failed to fetch session {session_id}: {e}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Return all session rows ordered by creation time (newest first).

        Returns:
            List of session dicts.
        """
        try:
            response = (
                self.client.table(TABLE_NAME)
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"[DB] Failed to list sessions: {e}")
            return []

    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update arbitrary columns on a session row.

        Example:
            db.update_session(session_id, interview_video="storage/path.mp4")
        """
        try:
            self.client.table(TABLE_NAME).update(kwargs).eq("id", session_id).execute()
            return True
        except Exception as e:
            print(f"[DB] Failed to update session {session_id}: {e}")
            return False

    def update_ocean_score(self, session_id: str, scores: Dict[str, float]) -> bool:
        """
        Persist OCEAN scores to the ocean_score JSONB column.

        Args:
            session_id: UUID of the session.
            scores: e.g. {"O": 3.2, "C": 4.1, "E": 2.8, "A": 3.9, "N": 1.5}
                    or {"Openness": 3.2, ...}
        """
        return self.update_session(session_id, ocean_score=scores)

    def reset(self):
        """Clear the in-memory active session reference."""
        self._active_session_id = None

    # ------------------------------------------------------------------ #
    #  Storage helpers                                                     #
    # ------------------------------------------------------------------ #

    def _storage_upload(
        self,
        storage_path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload bytes to Supabase Storage and return the storage path.

        Args:
            storage_path: Path inside the bucket, e.g. 'session_uuid/video.mp4'
            data:         Raw bytes to upload.
            content_type: MIME type.

        Returns:
            The bucket-relative storage path (use to build signed URLs later).
        """
        try:
            self.client.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            return storage_path
        except Exception as e:
            raise RuntimeError(
                f"[Storage] Upload failed for {storage_path}: {e}"
            ) from e

    def _get_public_url(self, storage_path: str) -> str:
        """Get the public URL for a stored file."""
        return self.client.storage.from_(BUCKET_NAME).get_public_url(storage_path)

    def _download_to_temp(self, storage_path: str, suffix: str = "") -> Path:
        """
        Download a file from Storage into a NamedTemporaryFile.

        Returns:
            Path to the temp file on disk (caller must delete when done).
        """
        try:
            data: bytes = self.client.storage.from_(BUCKET_NAME).download(storage_path)
        except Exception as e:
            raise RuntimeError(
                f"[Storage] Download failed for {storage_path}: {e}"
            ) from e

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tmp.write(data)
            tmp.flush()
            tmp_path = Path(tmp.name)
        finally:
            tmp.close()
        return tmp_path

    # ------------------------------------------------------------------ #
    #  Interviewee-side uploads                                            #
    # ------------------------------------------------------------------ #

    def upload_image(self, session_id: str, image_bytes: bytes) -> str:
        """
        Upload the candidate's aligned face image and save the URL.

        Args:
            session_id:  UUID of the session.
            image_bytes: JPEG/PNG bytes of the image.

        Returns:
            Public URL of the uploaded image.
        """
        storage_path = f"{session_id}/aligned_face.jpg"
        try:
            self._storage_upload(storage_path, image_bytes, "image/jpeg")
            url = self._get_public_url(storage_path)
            self.update_session(session_id, user_image_url=url)
            print(f"[Storage] Image uploaded → {url}")
            return url
        except Exception as e:
            print(f"[Storage] Image upload error: {e}")
            raise

    def upload_csv(self, session_id: str, local_csv_path: Path) -> str:
        """
        Upload the thermal-landmark CSV and save its storage path.

        Args:
            session_id:     UUID of the session.
            local_csv_path: Path to the local CSV file.

        Returns:
            Bucket-relative storage path saved in csv_path column.
        """
        storage_path = f"{session_id}/thermal_data.csv"
        try:
            with open(local_csv_path, "rb") as f:
                data = f.read()
            self._storage_upload(storage_path, data, "text/csv")
            self.update_session(session_id, csv_path=storage_path)
            print(f"[Storage] CSV uploaded → {storage_path}")
            return storage_path
        except Exception as e:
            print(f"[Storage] CSV upload error: {e}")
            raise

    def upload_video(self, session_id: str, local_video_path: Path) -> str:
        """
        Upload the raw interview video and save its storage path.

        This is a large file upload — uses chunked reading to avoid memory spikes.

        Args:
            session_id:       UUID of the session.
            local_video_path: Path to the local .mp4 / .avi file.

        Returns:
            Bucket-relative storage path saved in interview_video column.
        """
        local_video_path = Path(local_video_path)
        suffix = local_video_path.suffix or ".mp4"
        storage_path = f"{session_id}/interview_video{suffix}"
        mime_type, _ = mimetypes.guess_type(str(local_video_path))
        mime_type = mime_type or "video/mp4"

        try:
            with open(local_video_path, "rb") as f:
                data = f.read()
            self._storage_upload(storage_path, data, mime_type)
            self.update_session(session_id, interview_video=storage_path)
            print(f"[Storage] Video uploaded → {storage_path}")
            return storage_path
        except Exception as e:
            print(f"[Storage] Video upload error: {e}")
            raise

    # ------------------------------------------------------------------ #
    #  Interviewer-side downloads                                          #
    # ------------------------------------------------------------------ #

    def download_video(self, session_id: str) -> Path:
        """
        Download the interview video from Supabase Storage to a temp file.

        The interviewer alignment page passes this temp path to OpenCV/CameraManager.
        Caller is responsible for deleting the file when processing is complete.

        Args:
            session_id: UUID of the session.

        Returns:
            Path to a temporary file on disk containing the video bytes.

        Raises:
            RuntimeError if the session has no video or download fails.
        """
        session = self.get_session(session_id)
        if not session:
            raise RuntimeError(f"[DB] Session {session_id} not found.")

        storage_path = session.get("interview_video")
        if not storage_path:
            raise RuntimeError(
                f"[DB] Session {session_id} has no interview_video stored yet."
            )

        # Determine suffix from the stored path
        suffix = Path(storage_path).suffix or ".mp4"
        print(f"[Storage] Downloading video for session {session_id}…")
        tmp_path = self._download_to_temp(storage_path, suffix=suffix)
        print(f"[Storage] Video downloaded to temp: {tmp_path}")
        return tmp_path

    def download_csv(self, session_id: str) -> Path:
        """
        Download the thermal-landmark CSV from Supabase Storage to a temp file.

        Args:
            session_id: UUID of the session.

        Returns:
            Path to a temporary .csv file on disk.

        Raises:
            RuntimeError if the session has no csv_path or download fails.
        """
        session = self.get_session(session_id)
        if not session:
            raise RuntimeError(f"[DB] Session {session_id} not found.")

        storage_path = session.get("csv_path")
        if not storage_path:
            raise RuntimeError(
                f"[DB] Session {session_id} has no csv_path stored yet."
            )

        print(f"[Storage] Downloading CSV for session {session_id}…")
        tmp_path = self._download_to_temp(storage_path, suffix=".csv")
        print(f"[Storage] CSV downloaded to temp: {tmp_path}")
        return tmp_path

    # ------------------------------------------------------------------ #
    #  Interviewer-side report upload                                      #
    # ------------------------------------------------------------------ #

    def upload_report_pdf(self, session_id: str, pdf_bytes: bytes) -> str:
        """
        Upload the generated PDF report and save its public URL.

        Args:
            session_id: UUID of the session.
            pdf_bytes:  Raw PDF bytes.

        Returns:
            Public URL of the uploaded PDF stored in report_pdf_url column.
        """
        storage_path = f"{session_id}/report.pdf"
        try:
            self._storage_upload(storage_path, pdf_bytes, "application/pdf")
            url = self._get_public_url(storage_path)
            self.update_session(session_id, report_pdf_url=url)
            print(f"[Storage] PDF uploaded → {url}")
            return url
        except Exception as e:
            print(f"[Storage] PDF upload error: {e}")
            raise
