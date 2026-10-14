#!/usr/bin/env python3
"""Publish a verified release APK, or preserve the already-published installer.

Website deployments do not invoke Gradle. A release APK is an independently
built artifact in dist/android, never an offline content-pack member.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "dist/android"
REMOTE = "https://kiansheik.io/nhe-enga/downloads/"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def public_fingerprint():
    der = base64.b64decode(os.environ["OFFLINE_PUBLIC_KEY"], validate=True)
    return hashlib.sha256(der).hexdigest()


def package():
    metadata = json.loads((ROOT / "android/app/build/outputs/apk/release/output-metadata.json").read_text())
    if metadata["variantName"] != "release" or metadata["applicationId"] != "io.kiansheik.nheenga":
        raise ValueError("Only the release application can be published")
    element = metadata["elements"][0]
    source = ROOT / "android/app/build/outputs/apk/release" / element["outputFile"]
    if not 0 < source.stat().st_size <= 15 * 1024 * 1024:
        raise ValueError("Release APK exceeds the 15 MiB shell size budget")
    sdk = Path(os.environ.get("ANDROID_HOME") or os.environ["ANDROID_SDK_ROOT"])
    subprocess.run([str(sdk / "build-tools/35.0.0/apksigner"), "verify", "--verbose", str(source)], check=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / "nhe-enga.apk"
    shutil.copyfile(source, target)
    metadata = {"versionCode": element["versionCode"], "versionName": element["versionName"],
                "bytes": target.stat().st_size, "sha256": sha(target), "url": "nhe-enga.apk",
                "contentKeySha256": public_fingerprint()}
    (CACHE / "android.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Verified release staged at {target}")


def restore():
    """Fresh source checkout: recover installer without a native rebuild.

    A non-404 failure is fatal, rather than silently removing a published APK.
    This is the project's own HTTPS origin, not a URL supplied by metadata.
    """
    try:
        with urllib.request.urlopen(REMOTE + "android.json", timeout=30) as response:
            data = response.read(64 * 1024 + 1)
            if len(data) > 64 * 1024:
                raise ValueError("Invalid Android release metadata")
            metadata = json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise
    size = metadata["bytes"]
    if not isinstance(size, int) or not 0 < size <= 15 * 1024 * 1024:
        raise ValueError("Invalid APK size")
    CACHE.mkdir(parents=True, exist_ok=True)
    temporary = CACHE / "nhe-enga.apk.part"
    with urllib.request.urlopen(REMOTE + "nhe-enga.apk", timeout=60) as response, temporary.open("wb") as output:
        written = 0
        while chunk := response.read(64 * 1024):
            written += len(chunk)
            if written > size:
                raise ValueError("Published APK exceeds its metadata size")
            output.write(chunk)
    if temporary.stat().st_size != size or sha(temporary) != metadata["sha256"]:
        raise ValueError("Published APK checksum mismatch")
    temporary.replace(CACHE / "nhe-enga.apk")
    (CACHE / "android.json").write_bytes(data)
    return True


def stage(build):
    if os.environ.get("OFFLINE_SKIP_APK") == "1":
        print("APK preservation explicitly skipped (local preview only)")
        return
    if not (CACHE / "android.json").is_file() and not restore():
        print("No Android release published yet; download link stays hidden")
        return
    metadata = json.loads((CACHE / "android.json").read_text())
    apk = CACHE / "nhe-enga.apk"
    if not apk.is_file() or apk.stat().st_size != metadata["bytes"] or sha(apk) != metadata["sha256"]:
        raise ValueError("Local APK artifact mismatch; rebuild or restore it")
    key = os.environ.get("OFFLINE_SIGNING_KEY")
    if not key:
        raise ValueError("Publishing an APK requires OFFLINE_SIGNING_KEY for compatible content catalogs")
    public = subprocess.run(["openssl", "pkey", "-in", key, "-pubout", "-outform", "DER"], check=True, capture_output=True).stdout
    if hashlib.sha256(public).hexdigest() != metadata["contentKeySha256"]:
        raise ValueError("Content signing key does not match the APK's trusted key")
    destination = build / "downloads"
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("nhe-enga.apk", "android.json"):
        shutil.copyfile(CACHE / name, destination / name)
    (destination / "nhe-enga.apk.sha256").write_text(metadata["sha256"] + "  nhe-enga.apk\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path, nargs="?")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if args.package:
        package()
    elif args.build:
        stage(args.build)
    else:
        parser.error("Pass a Pages build directory or --package")
