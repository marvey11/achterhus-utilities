"""File manipulation engine handling collisions, moves, and copies."""

import shutil
from pathlib import Path

from codescape.util.fileutils import atomic_move

from document_router.core.models import ActionType, ProcessingJob
from document_router.core.utils import calculate_sha256


class DocumentProcessor:
    """Executes processing jobs with collision detection and safety checks."""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def execute_job(self, job: ProcessingJob) -> str:
        """Executes a single job and returns a status summary string."""
        action = job.metadata.action

        match action:
            case ActionType.IGNORE:
                reason = job.metadata.ignore_reason
                return f"IGNORE ({reason})" if reason is not None else "IGNORE"
            case ActionType.QUARANTINE:
                return self._quarantine(
                    job, job.metadata.quarantine_reason or "Parser quarantine"
                )
            case ActionType.COPY | ActionType.MOVE:
                resolved_target = self._resolve_collisions(job)

                if resolved_target is None:
                    # Collision check determined target is an identical file hash
                    return self._quarantine(
                        job, "Duplicate content detected (SHA-256 match)"
                    )

                if not self.dry_run:
                    resolved_target.parent.mkdir(parents=True, exist_ok=True)
                    if action == ActionType.MOVE:
                        atomic_move(
                            job.source_file_path, resolved_target, verify_hash=True
                        )
                    else:
                        shutil.copy2(str(job.source_file_path), str(resolved_target))

                return f"{action.name} -> {resolved_target.name}"

    def _resolve_collisions(self, job: ProcessingJob) -> Path | None:
        """Resolves target collisions using SHA-256 comparison and suffixing."""

        source = job.source_file_path
        target = job.resolve_target_path()

        if not target.exists():
            return target

        saved_hash = job.metadata.hash_sha256
        source_hash = saved_hash if saved_hash is not None else calculate_sha256(source)
        target_hash = calculate_sha256(target)

        if source_hash == target_hash:
            # Hash match indicates duplicate document content
            return None

        # Content differs: append counter suffix before extension
        stem = target.stem
        suffix = target.suffix
        counter = 1

        while True:
            candidate = target.with_name(f"{stem}_{counter:03}{suffix}")
            if not candidate.exists():
                return candidate
            if calculate_sha256(candidate) == source_hash:
                return None
            counter += 1

    def _quarantine(self, job: ProcessingJob, reason: str) -> str:
        """Moves file to quarantine folder with diagnostic reason."""
        quarantine_dir = job.source_base_path / ".quarantine" / job.metadata.provider
        target_path = quarantine_dir / job.source_file_path.name

        if not self.dry_run:
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            atomic_move(job.source_file_path, target_path, verify_hash=True)

        return f"QUARANTINED ({reason})"
