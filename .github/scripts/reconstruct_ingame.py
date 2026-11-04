#!/usr/bin/env python3
"""Rebuild the two FS25 mod ZIPs from a verified base and a small overlay.

Network input is read only. This program never calls GitHub publication APIs.
The workflow separately uploads outputs after every payload check has passed.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import zipfile
import zlib

ARCHIVE_NAMES = {"FS25_Rennebu_WIP.zip", "FS25_BuildingsOfNorway_WIP.zip"}
STAMP = (2026, 11, 4, 0, 0, 0)
BUFFER = 1024 * 1024
DEFAULT_SOURCE_ZLIB = "1.3.2"
ALLOWED_DOWNLOAD_HOSTS = {"github.com", "raw.githubusercontent.com"}


class BuildError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BuildError(message)


def relative_path(value: str, label: str) -> str:
    require(isinstance(value, str) and value != "", f"{label}: path must be a nonempty string")
    require("\\" not in value and "\x00" not in value and ":" not in value,
            f"{label}: unsafe path {value!r}")
    parts = value.split("/")
    require(not value.startswith("/") and all(x not in {"", ".", ".."} for x in parts),
            f"{label}: unsafe path {value!r}")
    require(str(PurePosixPath(value)) == value, f"{label}: path is not canonical")
    return value


def digest_file(path: Path) -> tuple[int, str]:
    count = 0
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(BUFFER), b""):
            count += len(chunk)
            h.update(chunk)
    return count, h.hexdigest()


def verify_digest(path: Path, record: dict, label: str) -> None:
    size, sha = digest_file(path)
    require(size == record["size"], f"{label}: size mismatch: {size} != {record['size']}")
    require(sha == record["sha256"], f"{label}: SHA-256 mismatch")


def validate_digest(record: dict, label: str) -> None:
    require(isinstance(record.get("size"), int) and record["size"] >= 0, f"{label}: invalid size")
    sha = record.get("sha256")
    require(isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha),
            f"{label}: invalid lowercase SHA-256")


def join_url(prefix: str, path: str) -> str:
    return prefix.rstrip("/") + "/" + quote(relative_path(path, "download path"), safe="/")


def download(url: str, destination: Path) -> None:
    parsed = urlparse(url)
    require(parsed.scheme == "https" and parsed.hostname in ALLOWED_DOWNLOAD_HOSTS,
            "Only HTTPS GitHub/raw.githubusercontent.com download sources are accepted")
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Rennebu-FS25-Release-Builder/1"})
    partial = destination.with_name(destination.name + ".download")
    try:
        with urlopen(request, timeout=90) as source, partial.open("wb") as target:
            shutil.copyfileobj(source, target, BUFFER)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def validate_manifest(manifest: dict) -> None:
    require(isinstance(manifest, dict), "Manifest must be a JSON object")
    validate_digest(manifest["base"], "base")
    overlay = manifest["overlay"]
    validate_digest(overlay, "overlay")
    require(relative_path(overlay["name"], "overlay name") == PurePosixPath(overlay["name"]).name,
            "Overlay name must not contain a directory")
    require(isinstance(overlay.get("parts"), list) and overlay["parts"], "Overlay parts are missing")
    part_names = []
    for part in overlay["parts"]:
        validate_digest(part, "overlay part")
        part_names.append(relative_path(part["name"], "part name"))
    require(len(part_names) == len(set(part_names)), "Duplicate overlay part names")
    require(sum(x["size"] for x in overlay["parts"]) == overlay["size"], "Overlay part sizes do not sum correctly")
    archives = manifest["archives"]
    require(isinstance(archives, list) and {x.get("name") for x in archives} == ARCHIVE_NAMES
            and len(archives) == 2, "Manifest must describe exactly the two named FS25 mod ZIPs")
    for archive in archives:
        validate_digest(archive, archive["name"])
        require(isinstance(archive.get("files"), list), "Archive files must be a list")
        paths = []
        for item in archive["files"]:
            validate_digest(item, "payload file")
            paths.append(relative_path(item["path"], "payload file"))
            relative_path(item["source_path"], "payload source")
            require(item["source"] in {"base", "overlay"}, "Invalid payload source")
        require(archive["entries"] == len(paths), "Archive entry count does not match file list")
        require(len(paths) == len(set(paths)), "Duplicate payload paths")
        require(len(paths) == len({x.casefold() for x in paths}), "Case-insensitive duplicate payload paths")
        require("modDesc.xml" in paths, "Each mod must contain modDesc.xml at its ZIP root")
    doc_names = []
    for document in manifest.get("documents", []):
        validate_digest(document, "document")
        name = relative_path(document["name"], "document name")
        require("/" not in name and name not in ARCHIVE_NAMES and name != "PUBLISHED_ARCHIVES.json",
                "Unsafe or reserved document name")
        relative_path(document.get("source_path", document.get("path", name)), "document source")
        doc_names.append(name)
    require(len(doc_names) == len(set(doc_names)), "Duplicate document names")


def unique_zip_entries(archive: zipfile.ZipFile, label: str) -> dict[str, zipfile.ZipInfo]:
    entries = archive.infolist()
    names = [entry.filename for entry in entries]
    require(len(names) == len(set(names)), f"{label}: duplicate source ZIP entries")
    return {entry.filename: entry for entry in entries}


def assemble_overlay(manifest: dict, prefix: str, scratch: Path) -> Path:
    target = scratch / manifest["overlay"]["name"]
    with target.open("wb") as joined:
        for part in manifest["overlay"]["parts"]:
            local = scratch / "parts" / relative_path(part["name"], "overlay part")
            download(join_url(prefix, part["name"]), local)
            verify_digest(local, part, f"overlay part {part['name']}")
            with local.open("rb") as stream:
                shutil.copyfileobj(stream, joined, BUFFER)
    verify_digest(target, manifest["overlay"], "joined overlay")
    return target


def make_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, STAMP)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    info._compresslevel = 6
    info.extract_version = 20
    info.create_version = 20
    info.flag_bits = 0
    info.internal_attr = 0
    return info


def validate_output(path: Path, plan: dict) -> None:
    """Read every output byte again: payload, CRC, order and all ZIP metadata."""
    expected = {item["path"]: item for item in plan["files"]}
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        require([x.filename for x in infos] == sorted(expected), f"{path.name}: unexpected entry list/order")
        require(archive.comment == b"", f"{path.name}: archive comment must be empty")
        for info in infos:
            label = f"{path.name}:{info.filename}"
            require(not info.is_dir(), f"{label}: directory entry is not permitted")
            require(info.date_time == STAMP and info.create_system == 3
                    and info.external_attr == 0o100644 << 16 and info.compress_type == zipfile.ZIP_DEFLATED
                    and info.extract_version == 20 and info.create_version == 20
                    and info.internal_attr == 0 and info.extra == b"" and info.comment == b"",
                    f"{label}: incorrect ZIP metadata")
            expected_flags = 0 if info.filename.isascii() else 0x800
            require(info.flag_bits == expected_flags, f"{label}: incorrect ZIP flags")
            h = hashlib.sha256()
            size = 0
            with archive.open(info, "r") as stream:
                for chunk in iter(lambda: stream.read(BUFFER), b""):
                    size += len(chunk)
                    h.update(chunk)
            require(size == expected[info.filename]["size"], f"{label}: output size mismatch")
            require(h.hexdigest() == expected[info.filename]["sha256"], f"{label}: output SHA-256 mismatch")
        # ZipExtFile checks CRC while reading; testzip explicitly records a full
        # archive CRC acceptance check as well.
        require(archive.testzip() is None, f"{path.name}: CRC validation failed")
        require("modDesc.xml" in archive.namelist(), f"{path.name}: missing root modDesc.xml")


def build_archive(plan: dict, sources: dict[str, zipfile.ZipFile],
                  source_entries: dict[str, dict[str, zipfile.ZipInfo]], output: Path,
                  expected_zlib: str) -> dict:
    destination = output / plan["name"]
    partial = destination.with_name(destination.name + ".partial")
    try:
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=False) as result:
            for item in sorted(plan["files"], key=lambda x: x["path"]):
                origin = sources[item["source"]]
                info = source_entries[item["source"]].get(item["source_path"])
                require(info is not None and not info.is_dir(), f"Missing payload source: {item['source_path']}")
                require(info.file_size == item["size"], f"Wrong source size: {item['source_path']}")
                h = hashlib.sha256()
                size = 0
                with origin.open(info, "r") as source, result.open(make_info(item["path"]), "w", force_zip64=False) as target:
                    for chunk in iter(lambda: source.read(BUFFER), b""):
                        target.write(chunk)
                        h.update(chunk)
                        size += len(chunk)
                require(size == item["size"] and h.hexdigest() == item["sha256"],
                        f"Payload source SHA-256/size mismatch: {item['source_path']}")
        validate_output(partial, plan)
        size, sha = digest_file(partial)
        exact_archive = (size == plan["size"] and sha == plan["sha256"])
        same_zlib = zlib.ZLIB_RUNTIME_VERSION == expected_zlib
        require(exact_archive or not same_zlib,
                f"{plan['name']}: ZIP digest differs despite the same zlib runtime")
        partial.replace(destination)
        return {"name": plan["name"], "entries": len(plan["files"]), "size": size, "sha256": sha,
                "expectedLocalSize": plan["size"], "expectedLocalSha256": plan["sha256"],
                "archiveMatchesLocal": exact_archive, "exactPayloadVerified": True,
                "crcVerified": True, "metadataVerified": True,
                "compressionRuntimeDiffers": not same_zlib}
    finally:
        partial.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Local reviewed manifest.json / plan.json")
    parser.add_argument("--base", type=Path, help="Verified local base ZIP; avoids base download")
    parser.add_argument("--overlay", type=Path, help="Verified local joined overlay ZIP; avoids part downloads")
    parser.add_argument("--documents", type=Path, help="Directory containing local release documents")
    parser.add_argument("--source-prefix", help="Immutable raw GitHub URL prefix for overlay parts and documents")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-zlib", help="Overrides manifest buildRuntime.zlib; default source runtime is 1.3.2")
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    expected_zlib = args.expected_zlib or manifest.get("buildRuntime", {}).get("zlib", DEFAULT_SOURCE_ZLIB)
    require(isinstance(expected_zlib, str) and expected_zlib, "Expected zlib runtime must be recorded")
    args.output.mkdir(parents=True, exist_ok=True)
    published_path = args.output / "PUBLISHED_ARCHIVES.json"
    published_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="rennebu-build-") as temporary:
        scratch = Path(temporary)
        base = args.base
        if base is None:
            base = scratch / "base.zip"
            download(manifest["base"]["url"], base)
        verify_digest(base, manifest["base"], "base archive")
        overlay = args.overlay
        if overlay is None:
            require(bool(args.source_prefix), "--source-prefix is required to download overlay parts")
            overlay = assemble_overlay(manifest, args.source_prefix, scratch)
        else:
            verify_digest(overlay, manifest["overlay"], "overlay archive")
        with ExitStack() as stack:
            sources = {"base": stack.enter_context(zipfile.ZipFile(base, "r")),
                       "overlay": stack.enter_context(zipfile.ZipFile(overlay, "r"))}
            source_entries = {name: unique_zip_entries(archive, name) for name, archive in sources.items()}
            reports = [build_archive(plan, sources, source_entries, args.output, expected_zlib)
                       for plan in manifest["archives"]]
        documents = []
        for document in manifest.get("documents", []):
            source_path = document.get("source_path", document.get("path", document["name"]))
            local = (args.documents or args.manifest.parent) / source_path
            destination = args.output / document["name"]
            if local.is_file():
                verify_digest(local, document, f"document {document['name']}")
                if local.resolve() != destination.resolve():
                    shutil.copyfile(local, destination)
            else:
                require(bool(args.source_prefix), f"Local document missing: {source_path}")
                download(join_url(args.source_prefix, source_path), destination)
                verify_digest(destination, document, f"document {document['name']}")
            documents.append({"name": document["name"], "size": document["size"], "sha256": document["sha256"]})
        report = {"status": "PASS", "payloadContent": "All planned file bytes, entry counts and ZIP metadata verified",
                  "manifestSha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                  "baseSha256": manifest["base"]["sha256"], "overlaySha256": manifest["overlay"]["sha256"],
                  "sourceBuildRuntime": manifest.get("buildRuntime", {"zlib": expected_zlib}),
                  "reconstructionRuntime": {"python": sys.version.split()[0], "zlib": zlib.ZLIB_RUNTIME_VERSION,
                                            "zlibCompileVersion": zlib.ZLIB_VERSION},
                  "archives": reports, "documents": documents,
                  "gameTested": False}
        published_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "archives": reports, "report": str(published_path)}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, KeyError, ValueError, OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        raise SystemExit(1)
