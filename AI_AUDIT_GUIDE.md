# AI Audit Guide

This guide helps users perform a quick independent review before running the Python script on their local machine.

## What To Audit

Review the core script:

- `ao3_backup_tool.py`

*(You can also audit `run.bat` and `list.txt`, though they only serve as a launcher and configuration input.)*

## Suggested AI Prompt

Copy and paste the code of `ao3_backup_tool.py` into any AI (like ChatGPT, Claude, Gemini) along with this prompt:

```text
Please audit this Python script as a security and privacy review before I run it on my machine.

Context:
This project is an AO3 (Archive of Our Own) fanfiction downloading tool. Some behavior is expected and should not be treated as malicious by itself:
- The script uses the `urllib` standard library to make HTTP GET requests to `archiveofourown.org` and `download.archiveofourown.org`.
- The script sends custom HTTP headers (like a spoofed Chrome `User-Agent` and a `Referer` header) to avoid being blocked by Cloudflare.
- The script uses `time.sleep()` to artificially delay network requests. This is an anti-bot mitigation feature to prevent server strain.
- The script creates a local directory named `works/` and writes binary files (.epub, .pdf, etc.) into it.
- The script uses Regular Expressions (re) to parse HTML tags and extract work metadata.

Please distinguish expected behavior from suspicious behavior. Do not label expected behavior as malware unless the code sends data to unrelated third-party servers, hides network calls, obfuscates logic, downloads executable code, accesses sensitive local files outside of its scope, or performs destructive actions.

1. Identify every external domain or IP address contacted.
2. Identify every directory or file system path the script reads from or writes to.
3. Check whether the code sends any local data, user preferences, or file contents to any third-party telemetry or analytics server.
4. Check for `eval`, `exec`, dynamic script loading, obfuscation, hidden network calls, or suspicious behavior.
5. Explain the metadata extraction logic, the duplication checking logic, and the OS-safe filename sanitization in plain language.
6. Classify each finding as one of: expected behavior, privacy risk, security risk, or unclear.
7. List any real risks and explain whether they are inherent to this kind of automation script or avoidable in this codebase.

Do not rewrite the code unless I ask. Focus on security, privacy, data flow, and objective risk classification.
```

## Expected Safe Shape

- `ao3_backup_tool.py` should only connect to `archiveofourown.org` and its official download subdomain.
- The script should only read from `list.txt` in the current directory.
- The script should only write to the `works/` subdirectory.
- The script should **never** send telemetry, analytics, or user data to servers controlled by the project author or third parties.
- The script should only use Python's built-in Standard Library modules (no third-party packages installed via `pip`).
- No `eval`, `exec`, remote script execution, hidden trackers, or unrelated domains should appear.
- Spoofing the `User-Agent` header and implementing `time.sleep()` cooldowns are expected and necessary for Cloudflare compatibility, but users should still verify that these mechanisms are limited to their stated purpose.

## Important Limit

AI review is highly helpful for transparency, but it is not a perfect security guarantee. Users should always read the code, verify the network domains, and understand what a script does before executing it on their local environment.
