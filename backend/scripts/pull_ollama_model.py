"""Download an Ollama model into the standard Ollama volume.

The official CLI occasionally receives an EOF from the model registry on some
Docker Desktop networks.  This small, retrying bootstrap uses the public
registry API directly and writes the exact manifest/blob layout consumed by
the local Ollama server.  No model data is sent to a third-party AI service.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


REGISTRY = "https://registry.ollama.ai"
RETRIES = 5
CHUNK_SIZE = 1024 * 1024


def model_reference() -> tuple[str, str]:
    """Return the Ollama repository path and tag for the configured model."""

    configured_model = os.environ.get("OLLAMA_MODEL", "llama3.2:1b").strip()
    if not configured_model:
        raise ValueError("OLLAMA_MODEL non è configurato.")
    name, separator, tag = configured_model.rpartition(":")
    if not separator:
        name, tag = configured_model, "latest"
    repository = name if "/" in name else f"library/{name}"
    return repository, tag


def request_bytes(url: str, *, accept: str = "application/octet-stream") -> bytes:
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "TicketHub-Ollama-bootstrap/1.0",
        },
    )
    with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed public registry URL
        return response.read()


def download_blob(url: str, destination: Path, expected_size: int) -> None:
    """Download one content-addressed blob atomically, retrying transient errors."""

    if destination.exists() and destination.stat().st_size == expected_size:
        print(f"Using cached blob {destination.name}", flush=True)
        return

    for attempt in range(1, RETRIES + 1):
        temporary_destination = destination.with_suffix(".part")
        temporary_destination.unlink(missing_ok=True)
        try:
            request = Request(url, headers={"User-Agent": "TicketHub-Ollama-bootstrap/1.0"})
            with urlopen(request, timeout=60) as response, temporary_destination.open("wb") as output:  # noqa: S310
                downloaded = 0
                next_progress = 100 * CHUNK_SIZE
                while chunk := response.read(CHUNK_SIZE):
                    output.write(chunk)
                    downloaded += len(chunk)
                    if downloaded >= next_progress:
                        print(f"Downloaded {downloaded // CHUNK_SIZE} MiB of {destination.name}", flush=True)
                        next_progress += 100 * CHUNK_SIZE
            if downloaded != expected_size:
                raise ValueError(f"Dimensione inattesa: {downloaded} byte, attesi {expected_size}.")
            temporary_destination.replace(destination)
            print(f"Downloaded {destination.name}", flush=True)
            return
        except (OSError, URLError, ValueError) as error:
            temporary_destination.unlink(missing_ok=True)
            if attempt == RETRIES:
                raise RuntimeError(f"Download fallito per {destination.name}: {error}") from error
            print(f"Download fallito (tentativo {attempt}/{RETRIES}): {error}", flush=True)
            time.sleep(attempt * 3)


def main() -> None:
    repository, tag = model_reference()
    manifest_url = f"{REGISTRY}/v2/{repository}/manifests/{tag}"
    manifest_bytes = request_bytes(
        manifest_url,
        accept="application/vnd.ollama.image.manifest.v2+json, application/json",
    )
    manifest: dict[str, Any] = json.loads(manifest_bytes)
    descriptors = [manifest["config"], *manifest["layers"]]

    models_root = Path(os.environ.get("OLLAMA_MODELS", "/root/.ollama/models"))
    blobs_directory = models_root / "blobs"
    manifest_path = models_root / "manifests" / "registry.ollama.ai" / repository / tag
    blobs_directory.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Preparing Ollama model {repository}:{tag}", flush=True)
    for descriptor in descriptors:
        digest = str(descriptor["digest"])
        size = int(descriptor["size"])
        if not digest.startswith("sha256:"):
            raise ValueError(f"Digest non supportato: {digest}")
        blob_path = blobs_directory / digest.replace(":", "-")
        download_blob(f"{REGISTRY}/v2/{repository}/blobs/{digest}", blob_path, size)

    manifest_path.write_bytes(manifest_bytes)
    print(f"Ollama model {repository}:{tag} is ready.", flush=True)


if __name__ == "__main__":
    main()
