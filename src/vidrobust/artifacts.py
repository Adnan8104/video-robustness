"""Checksum-verified local artifacts and downloads."""
import hashlib
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
