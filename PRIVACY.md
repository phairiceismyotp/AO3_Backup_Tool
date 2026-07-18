# Privacy Policy

**AO3 Backup Tool** is a local Python script designed with user privacy and security as fundamental principles. 

## Data Collection and Transmission
- **Zero Telemetry:** This tool does not collect, store, or transmit any analytics, crash reports, usage statistics, or telemetry data to the developer or any third parties.
- **Local Execution:** All processing occurs entirely on your local machine.
- **Network Requests:** The tool only connects to `archiveofourown.org` and `download.archiveofourown.org` to fetch metadata and download fanfiction files. No background connections are made to any other servers.

## Personal Information
- **No Credentials Required:** The script does not require, prompt for, or handle your AO3 account credentials. It is designed to work exclusively with public (unlocked) works.
- **Anonymity:** The tool utilizes spoofed, generic `User-Agent` headers. This protects your actual browser, operating system, and hardware information from being accurately fingerprinted by the destination server during scraping.

## File System Access
- **Restricted Scope:** The script only reads from the specifically designated input file (`list.txt`) and only writes downloaded files to the designated output directory (`works/`). It does not scan, index, or access any other directories on your hard drive.

By using this tool, you can be completely assured that your downloading habits, IP address, and fanfiction preferences remain strictly between your personal machine and Archive of Our Own.
