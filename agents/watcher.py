"""File system watcher with GitPython integration — zero LLM calls."""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Optional

import git
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from watchdog.observers import Observer

from models.schemas import ChangeEvent

logger = logging.getLogger(__name__)

# File extensions to monitor
MONITORED_EXTENSIONS = {".py", ".ts", ".js", ".go", ".java"}

# Paths to ignore
IGNORE_PATHS = {".git", "docs", "__pycache__", ".qdrant", ".venv"}


class DocuMindEventHandler(FileSystemEventHandler):
    """Watchdog handler that filters for code files and ignores system directories."""

    def __init__(self, repo: git.Repo, event_queue: Queue, debounce_seconds: float = 2.0):
        super().__init__()
        self.repo = repo
        self.event_queue = event_queue
        self.debounce_seconds = debounce_seconds
        self.last_commit_hash: Optional[str] = None
        self.last_event_time: float = 0.0

    def _should_process(self, event) -> bool:
        """Check if event should be processed."""
        # Only process file modifications and creations
        if not isinstance(event, (FileModifiedEvent, FileCreatedEvent)):
            return False

        # Skip directories
        if event.is_directory:
            return False

        # Check file extension
        file_path = Path(event.src_path)
        if file_path.suffix not in MONITORED_EXTENSIONS:
            return False

        # Check if path contains ignored directories
        path_parts = file_path.parts
        if any(ignored in path_parts for ignored in IGNORE_PATHS):
            return False

        return True

    def _extract_change_event(self) -> Optional[ChangeEvent]:
        """Extract git change information and build ChangeEvent."""
        try:
            # Get current commit
            current_commit = self.repo.head.commit

            # Skip if same commit as last processed
            if current_commit.hexsha == self.last_commit_hash:
                logger.debug(f"Skipping duplicate commit {current_commit.hexsha[:8]}")
                return None

            # Get changed files
            try:
                # Try diff against previous commit
                diff_index = current_commit.diff("HEAD~1")
                diff_text = self.repo.git.diff("HEAD~1", "HEAD")
            except git.exc.GitCommandError:
                # Fallback for initial commit (no HEAD~1)
                logger.info("No previous commit found, using HEAD diff")
                diff_index = current_commit.diff(git.NULL_TREE)
                diff_text = self.repo.git.diff(git.NULL_TREE, "HEAD")

            # Extract changed file paths
            files_changed = [item.a_path or item.b_path for item in diff_index]

            # Build ChangeEvent
            change_event = ChangeEvent(
                files_changed=files_changed,
                diff=diff_text,
                commit_msg=current_commit.message.strip(),
                commit_hash=current_commit.hexsha,
                timestamp=datetime.fromtimestamp(current_commit.committed_date).isoformat(),
                author=current_commit.author.name,
            )

            # Update last processed commit
            self.last_commit_hash = current_commit.hexsha

            logger.info(
                f"Extracted ChangeEvent: {len(files_changed)} files, "
                f"commit {current_commit.hexsha[:8]}"
            )
            return change_event

        except Exception as e:
            logger.error(f"Failed to extract change event: {e}")
            return None

    def on_modified(self, event):
        """Handle file modification events."""
        if not self._should_process(event):
            return

        current_time = time.time()

        # Debounce: wait for git commit to complete
        if current_time - self.last_event_time < self.debounce_seconds:
            logger.debug(f"Debouncing event for {event.src_path}")
            return

        self.last_event_time = current_time

        logger.info(f"File modified: {event.src_path}")

        # Wait for git commit to complete
        time.sleep(self.debounce_seconds)

        # Extract change event
        change_event = self._extract_change_event()
        if change_event:
            self.event_queue.put(change_event)
            logger.info(f"ChangeEvent queued: {change_event.commit_hash[:8]}")

    def on_created(self, event):
        """Handle file creation events."""
        # Use same logic as modification
        self.on_modified(event)


class WatcherAgent:
    """File system watcher with GitPython integration."""

    def __init__(self, watch_dir: Optional[str] = None, debounce_seconds: float = 2.0):
        """
        Initialize watcher agent.

        Args:
            watch_dir: Directory to watch (defaults to WATCH_DIR env var or current dir)
            debounce_seconds: Seconds to wait after file change before processing
        """
        self.watch_dir = watch_dir or os.getenv("WATCH_DIR", ".")
        self.watch_dir = os.path.abspath(self.watch_dir)
        self.debounce_seconds = debounce_seconds

        # Initialize git repo
        try:
            self.repo = git.Repo(self.watch_dir, search_parent_directories=True)
            logger.info(f"Git repo found: {self.repo.working_dir}")
        except git.exc.InvalidGitRepositoryError:
            raise ValueError(f"Not a git repository: {self.watch_dir}")

        # Event queue (thread-safe)
        self.event_queue: Queue[ChangeEvent] = Queue()

        # Watchdog observer
        self.observer = Observer()
        self.event_handler = DocuMindEventHandler(
            self.repo, self.event_queue, self.debounce_seconds
        )

        logger.info(f"WatcherAgent initialized for {self.watch_dir}")

    def start(self):
        """Start watching the directory."""
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=True)
        self.observer.start()
        logger.info(f"Started watching {self.watch_dir}")

    def stop(self):
        """Stop watching the directory."""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped watching")

    def get_event(self, timeout: Optional[float] = None) -> Optional[ChangeEvent]:
        """
        Get next ChangeEvent from queue.

        Args:
            timeout: Seconds to wait for event (None = non-blocking)

        Returns:
            ChangeEvent if available, None otherwise
        """
        try:
            if timeout is None:
                # Non-blocking
                return self.event_queue.get_nowait()
            else:
                # Blocking with timeout
                return self.event_queue.get(timeout=timeout)
        except Exception:
            return None


# Made with Bob