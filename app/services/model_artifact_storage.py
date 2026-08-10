"""Trusted local storage for server-created model artifact binary payloads."""

import os
from pathlib import Path
from uuid import UUID


class ModelArtifactStorageError(ValueError):
    pass


class LocalModelArtifactStorage:
    """Stores only internally generated company/artifact references below one base directory."""

    def __init__(self, base_directory: str | Path | None = None):
        configured = base_directory or os.getenv("MODEL_ARTIFACT_STORAGE_DIR")
        self.base_directory = Path(configured or Path.cwd() / ".model_artifacts").resolve()

    def write(self, company_id: UUID, artifact_id: UUID, payload: bytes) -> str:
        if not isinstance(payload, bytes):
            raise ModelArtifactStorageError("artifact payload must be bytes")
        reference = f"{company_id}/{artifact_id}.ubj"
        path = self._path(reference)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ModelArtifactStorageError("artifact storage reference already exists")
        path.write_bytes(payload)
        return reference

    def read(self, reference: str) -> bytes:
        path = self._path(reference)
        if not path.is_file():
            raise ModelArtifactStorageError("artifact payload does not exist")
        return path.read_bytes()

    def exists(self, reference: str) -> bool:
        return self._path(reference).is_file()

    def delete_for_controlled_cleanup(self, reference: str) -> None:
        path = self._path(reference)
        if path.exists():
            path.unlink()
        parent = path.parent
        if parent != self.base_directory and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    def _path(self, reference: str) -> Path:
        parts = reference.split("/") if isinstance(reference, str) else []
        if len(parts) != 2 or not parts[1].endswith(".ubj"):
            raise ModelArtifactStorageError("invalid controlled artifact reference")
        try:
            UUID(parts[0])
            UUID(parts[1][:-4])
        except ValueError as exc:
            raise ModelArtifactStorageError("invalid controlled artifact reference") from exc
        path = (self.base_directory / parts[0] / parts[1]).resolve()
        if self.base_directory not in path.parents:
            raise ModelArtifactStorageError("artifact path escapes controlled storage")
        return path
