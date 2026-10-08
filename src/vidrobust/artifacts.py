"""Checksum-verified local artifacts and downloads."""
import hashlib
from pathlib import Path
import re
from urllib.parse import quote, urlsplit
import urllib.request


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest, expected):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and sha(dest) == expected:
        return
    tmp = dest.with_suffix(".part")
    print(f"Downloading {dest.name}", flush=True)
    urllib.request.urlretrieve(url, tmp)
    if sha(tmp) != expected:
        tmp.unlink()
        raise ValueError(f"Checksum mismatch: {dest}")
    tmp.replace(dest)


def source_url(sample):
    """Resolve pinned HF files or explicitly attributed public HTTPS sources."""
    provider = sample.get("provider", "huggingface")
    if provider == "huggingface":
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", sample.get("dataset", "")):
            raise ValueError("Invalid Hugging Face dataset")
        if not re.fullmatch(r"[0-9a-f]{40}", sample.get("revision", "")):
            raise ValueError("Hugging Face source needs a pinned dataset commit")
        remote = sample.get("remote_path", "")
        if not remote or Path(remote).is_absolute() or ".." in Path(remote).parts:
            raise ValueError("Invalid remote path")
        return f"https://huggingface.co/datasets/{sample['dataset']}/resolve/{sample['revision']}/{quote(remote, safe='/')}"
    if provider != "http":
        raise ValueError("Unknown source provider")
    for key in ("source_url", "source_page"):
        value = sample.get(key, "")
        parts = urlsplit(value)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.fragment:
            raise ValueError("Public sources need HTTPS media and attribution URLs without credentials/fragments")
    revision = sample.get("source_revision")
    if not isinstance(revision, str) or not revision.strip() or len(revision) > 160:
        raise ValueError("Public source needs a recorded source revision/version")
    return sample["source_url"]
