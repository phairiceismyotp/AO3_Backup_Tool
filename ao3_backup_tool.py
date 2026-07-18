#!/usr/bin/env python3
"""
AO3 Backup Tool
===============
Automates the retrieval of fanfiction works from Archive of Our Own (AO3)
using the site's direct download endpoint.

This script fetches each work's HTML page to extract 100% of the full
work title and author name before initiating the download.

Usage:
  1. Populate list.txt with work IDs or AO3 URLs, one per line.
  2. Run this script: python ao3_backup_tool.py
  3. Downloaded files are saved to the works/ subdirectory.

Author: phairiceismyotp (or3zz - Nguyen Tin)
Dependencies: Python 3.10+ standard library only (no third-party packages).
"""

import http.client
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --- Configuration -----------------------------------------------------------

# AO3's direct download endpoint. {work_id} and {fmt} are substituted at runtime.
BASE_DOWNLOAD_URL: str = "https://download.archiveofourown.org/downloads/{work_id}/fic.{fmt}"

# Delays (in seconds) between requests to satisfy Cloudflare rate-limiting checks.
METADATA_DELAY_SECONDS: int = 3
DOWNLOAD_DELAY_SECONDS: int = 7

# Path to the input file, resolved relative to this script's directory.
LIST_FILE: str = "list.txt"

# Output directory for downloaded files, relative to this script's directory.
OUTPUT_DIR: str = "works"

# All formats supported by the AO3 download endpoint.
FORMATS: list[str] = ["azw3", "epub", "mobi", "pdf", "html"]

# Chrome major version used in the User-Agent string.
CHROME_VERSION: int = 150

# Standard HTTP headers for Cloudflare bypass.
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://archiveofourown.org/",
}

# --- Utilities ---------------------------------------------------------------

def extract_work_id(raw: str) -> str | None:
    """
    Extract the numeric work ID from a raw input string.

    Accepts any of the following input forms:
      - Bare numeric ID:    22402597
      - Full AO3 URL:       https://archiveofourown.org/works/22402597/chapters/...
      - AO3 download URL:   https://download.archiveofourown.org/downloads/22402597/...

    Args:
        raw (str): The raw input string containing the work ID or URL.

    Returns:
        str | None: The work ID as a string, or None if the input cannot be parsed.
    """
    raw = raw.strip()
    if not raw:
        return None

    # Match /works/<id> found in standard AO3 work URLs
    m = re.search(r"/works/(\d+)", raw)
    if m:
        return m.group(1)

    # Match /downloads/<id> found in AO3 download URLs
    m = re.search(r"/downloads/(\d+)", raw)
    if m:
        return m.group(1)

    # Accept a bare numeric string as a work ID directly
    if re.fullmatch(r"\d+", raw):
        return raw

    return None


def build_url(work_id: str, fmt: str) -> str:
    """
    Construct the AO3 download URL for the given work ID and format.

    Args:
        work_id (str): The numeric ID of the AO3 work.
        fmt (str): The desired file format extension (e.g., 'epub', 'pdf').

    Returns:
        str: The fully formatted download URL.
    """
    return BASE_DOWNLOAD_URL.format(work_id=work_id, fmt=fmt)


def sanitize_filename(name: str) -> str:
    """
    Replace filesystem-unsafe characters and reserved names in a filename.

    Args:
        name (str): The original filename to be sanitized.

    Returns:
        str: A safe filename string compatible with Windows filesystems.
    """
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    sanitized = sanitized.rstrip(". ")
    
    # Block Windows reserved filenames (checks the base name before extension)
    reserved = {
        "CON", "PRN", "AUX", "NUL", 
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", 
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    base_name = sanitized.split(".")[0].upper()
    if base_name in reserved:
        sanitized = "file_" + sanitized
        
    return sanitized or "unnamed_work"


def fetch_work_title(work_id: str) -> str | None:
    """
    Fetch the work page and extract the full work title and author name.

    Args:
        work_id (str): The numeric ID of the AO3 work.

    Returns:
        str | None: A sanitized filename string in the format "Title - Author",
            or None if the metadata cannot be retrieved.
    """
    url = f"https://archiveofourown.org/works/{work_id}"
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="ignore")

        title_match = re.search(r'<h2[^>]*class=["\']title heading["\'][^>]*>\s*(.*?)\s*</h2>', html, re.DOTALL)
        title = title_match.group(1).strip() if title_match else None

        if not title:
            return None

        byline_match = re.search(r'<h3[^>]*class=["\']byline heading["\'][^>]*>\s*(.*?)\s*</h3>', html, re.DOTALL)
        if byline_match:
            author = re.sub(r'<[^>]+>', '', byline_match.group(1)).strip()
            author = re.sub(r'\s+', ' ', author)
        else:
            author = ""

        if author and author != "Anonymous":
            full_name = f"{title} - {author}"
        else:
            full_name = title

        return sanitize_filename(full_name)
    except (urllib.error.URLError, TimeoutError, ValueError, http.client.IncompleteRead):
        return None


def download_file(url: str, dest: Path, use_custom_name: bool = False) -> None:
    """
    Fetch the file at the given URL and write it to the destination path.

    If `use_custom_name` is True, the `dest` path is used as-is. Otherwise,
    the filename is extracted from the Content-Disposition header.

    Args:
        url (str): The direct download URL.
        dest (Path): The target file path.
        use_custom_name (bool, optional): Whether to strictly use the provided
            dest path. Defaults to False.
    """
    headers = DEFAULT_HEADERS.copy()
    headers["Upgrade-Insecure-Requests"] = "1"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        if not use_custom_name:
            content_disp = response.headers.get("Content-Disposition", "")
            match_utf8 = re.search(r"filename\*\s*=\s*utf-8''([^;\r\n]+)", content_disp, re.IGNORECASE)
            if match_utf8:
                fname = urllib.parse.unquote(match_utf8.group(1).strip())
                dest = dest.parent / sanitize_filename(fname)
            else:
                match = re.search(r'filename=["\']?([^"\';\r\n]+)', content_disp)
                if match:
                    fname = match.group(1).strip().rstrip('"\'')
                    dest = dest.parent / sanitize_filename(fname)

        content = response.read()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    print(f"  [OK]   Saved: {dest.name}")

# --- User interface ----------------------------------------------------------

def print_banner() -> None:
    """
    Print the application header to standard output.
    """
    print("\n  +--------------------------------------------------+")
    print("  |                 AO3 BACKUP TOOL                  |")
    print("  +--------------------------------------------------+\n")


def choose_format() -> str | None:
    """
    Prompt the user to select a download format from the available options.

    Returns:
        str | None: The selected format string (e.g., 'epub'), or None if
            the user chooses to exit.
    """
    print("  Select a download format:")
    for i, fmt in enumerate(FORMATS, 1):
        print(f"    {i}. {fmt.upper()}")
    print("    0. Exit\n")

    while True:
        try:
            raw = input("  > Enter number (0-5): ").strip()
            idx = int(raw)
            if idx == 0:
                return None
            if 1 <= idx <= len(FORMATS):
                chosen = FORMATS[idx - 1]
                print(f"  [OK]   Format selected: {chosen.upper()}\n")
                return chosen
            print("  [!]   Please enter a number between 0 and 5.")
        except ValueError:
            print("  [!]   Invalid input. Enter a whole number.")
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Interrupted by user.")
            sys.exit(0)


def read_list(path: Path) -> list[str]:
    """
    Read and return non-empty, non-comment lines from the input file.

    Lines beginning with '#' are treated as comments and ignored.

    Args:
        path (Path): The path to the input text file.

    Returns:
        list[str]: A list of raw work entries.
    
    Raises:
        SystemExit: If the file does not exist.
    """
    if not path.exists():
        print(f"  [!]   Input file not found: {path}")
        print(f"  [>]   Create '{LIST_FILE}' in the same directory as this script and try again.")
        sys.exit(1)

    entries = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line)
    return entries

# --- Main logic --------------------------------------------------------------

def process_single_work(work_id: str, fmt: str, out_dir: Path, task_num: int, total_valid: int) -> bool:
    """
    Process a single work: fetch metadata, apply delay, and download file.

    Args:
        work_id (str): The numeric ID of the AO3 work.
        fmt (str): The selected download format.
        out_dir (Path): The directory to save downloaded files.
        task_num (int): The current task index (for display).
        total_valid (int): The total number of valid tasks (for display).

    Returns:
        bool: True if successful or file already exists, False if the download fails.
    """
    print(f"  [{task_num}/{total_valid}] work_id={work_id}")

    title_name = fetch_work_title(work_id)
    if title_name:
        dest = out_dir / f"{title_name}.{fmt}"
        use_custom_name = True
    else:
        dest = out_dir / f"{work_id}.{fmt}"
        use_custom_name = False

    time.sleep(METADATA_DELAY_SECONDS)

    url = build_url(work_id, fmt)
    print(f"         {url}")

    if dest.exists():
        print(f"  [--]   Already exists, skipping: {dest.name}")
        return True

    try:
        download_file(url, dest, use_custom_name=use_custom_name)
        return True
    except urllib.error.HTTPError as e:
        print(f"  [!]   HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"  [!]   Connection error: {e.reason}")
    except Exception as e:
        print(f"  [!]   Unexpected error: {e}")

    return False


def run() -> None:
    """
    Entry point for the main application loop.

    Initializes the output directory, reads entries, fetches metadata,
    and downloads files sequentially with configurable pauses.
    """
    print_banner()

    base_dir = Path(__file__).parent
    list_path = base_dir / LIST_FILE
    out_dir = base_dir / OUTPUT_DIR
    out_dir.mkdir(exist_ok=True)

    while True:
        fmt = choose_format()
        if fmt is None:
            print("  Goodbye.")
            sys.exit(0)

        raw_entries = read_list(list_path)
        print(f"  [i]   Found {len(raw_entries)} entr{'y' if len(raw_entries) == 1 else 'ies'} in {LIST_FILE}.\n")

        valid_count = sum(1 for e in raw_entries if extract_work_id(e))

        if valid_count == 0:
            print("  [!]   No recognizable work entries found. Please check list.txt.\n")
            continue

        print(f"  [>]   Downloading {valid_count} work(s) to '{OUTPUT_DIR}/'.")
        print(f"        Pauses: {METADATA_DELAY_SECONDS}s after metadata, {DOWNLOAD_DELAY_SECONDS}s after download.\n")

        success_count = 0
        fail_count = 0
        task_num = 0

        for entry in raw_entries:
            work_id = extract_work_id(entry)

            if not work_id:
                print(f"  [skip] Unrecognized entry: {entry}\n")
                continue

            task_num += 1
            is_success = process_single_work(work_id, fmt, out_dir, task_num, valid_count)
            
            if is_success:
                success_count += 1
            else:
                fail_count += 1

            if task_num < valid_count:
                print(f"  ...    Waiting {DOWNLOAD_DELAY_SECONDS}s before next work.\n")
                time.sleep(DOWNLOAD_DELAY_SECONDS)
            else:
                print()

        print("  " + "-" * 40)
        print("  Session complete.")
        print(f"    Succeeded : {success_count}")
        if fail_count:
            print(f"    Failed    : {fail_count}")
        print(f"    Output    : {out_dir.resolve()}\n")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
        sys.exit(0)
