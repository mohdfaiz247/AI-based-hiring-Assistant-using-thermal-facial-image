"""
AI Hiring Assistant - Data Manager
Handles all local file I/O operations using pathlib for cross-platform compatibility.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class DataManager:
    """
    Manages all local data storage operations.
    All data is stored in ./user_data/{session_id}/ directory structure.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the DataManager.
        
        Args:
            base_path: Optional base path for user_data. Defaults to ./user_data
        """
        if base_path is None:
            # Check for Docker environment variable mapping first
            env_path = os.getenv("USER_DATA_DIR")
            if env_path:
                self.base_path = Path(env_path)
            else:
                # Use the shared user_data directory in interviewer_side/AIHiringAssistant
                # Assuming CWD is the aaryan'gui directory where main.py is located
                self.base_path = Path.cwd().parent / "interviewer_side" / "AIHiringAssistant" / "user_data"
        else:
            self.base_path = Path(base_path)
        
        self.session_id: Optional[str] = None
        self.session_path: Optional[Path] = None
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID based on current timestamp."""
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new session directory.
        
        Args:
            session_id: Optional custom session ID. Auto-generated if not provided.
            
        Returns:
            The session ID used.
        """
        if session_id is None:
            session_id = self.generate_session_id()
        
        self.session_id = session_id
        self.session_path = self.base_path / session_id
        
        # Create the session directory
        try:
            self.session_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create session directory: {e}")
        
        return session_id
    
    def _ensure_session(self):
        """Ensure a session has been created."""
        if self.session_path is None:
            raise RuntimeError("No active session. Call create_session() first.")
    
    def save_registration(self, data: Dict[str, Any]) -> Path:
        """
        Save registration data to registration.json.
        
        Args:
            data: Dictionary containing registration fields.
            
        Returns:
            Path to the saved file.
        """
        self._ensure_session()
        
        file_path = self.session_path / "registration.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Failed to save registration data: {e}")
        
        return file_path
    
    def save_assessment(self, responses: Dict[str, List[int]]) -> Path:
        """
        Save OCEAN assessment responses to assessment.json.
        
        Args:
            responses: Dictionary with trait names as keys and list of responses as values.
            
        Returns:
            Path to the saved file.
        """
        self._ensure_session()
        
        # Calculate scores (mean of each trait's responses)
        scores = {}
        for trait, values in responses.items():
            if values:
                scores[trait] = round(sum(values) / len(values), 2)
            else:
                scores[trait] = 0.0
        
        assessment_data = {
            "responses": responses,
            "scores": scores,
            "timestamp": datetime.now().isoformat()
        }
        
        file_path = self.session_path / "assessment.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(assessment_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Failed to save assessment data: {e}")
        
        return file_path
    
    def get_interview_path(self, question_id: int) -> Path:
        """
        Get the file path for an interview recording.
        
        Args:
            question_id: The ID of the interview question.
            
        Returns:
            Path where the interview video should be saved.
        """
        self._ensure_session()
        return self.session_path / f"interview_{question_id}.mp4"
    
    def get_interview_recordings(self) -> List[str]:
        """
        Get list of all interview recording paths in the session.
        
        Returns:
            List of relative paths to interview recordings.
        """
        self._ensure_session()
        
        recordings = []
        for file in self.session_path.glob("interview_*.mp4"):
            recordings.append(str(file.relative_to(self.base_path.parent)))
        
        return sorted(recordings)
    
    def save_summary(self, registration: Dict[str, Any], 
                     assessment_scores: Dict[str, float]) -> Path:
        """
        Save the final summary to summary.json.
        
        Args:
            registration: Registration data dictionary.
            assessment_scores: Dictionary of OCEAN trait scores.
            
        Returns:
            Path to the saved file.
        """
        self._ensure_session()
        
        # Collect all interview recordings
        recordings = self.get_interview_recordings()
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "registration": registration,
            "interview_recordings": recordings,
            "ocean_scores": assessment_scores
        }
        
        file_path = self.session_path / "summary.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Failed to save summary: {e}")
        
        return file_path
    
    def load_registration(self) -> Optional[Dict[str, Any]]:
        """Load registration data if it exists."""
        self._ensure_session()
        
        file_path = self.session_path / "registration.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
    
    def load_assessment(self) -> Optional[Dict[str, Any]]:
        """Load assessment data if it exists."""
        self._ensure_session()
        
        file_path = self.session_path / "assessment.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
    
    def reset(self):
        """Reset the manager for a new session (does not delete files)."""
        self.session_id = None
        self.session_path = None
    
    def get_session_folder(self) -> Optional[Path]:
        """Get the current session folder path."""
        return self.session_path
