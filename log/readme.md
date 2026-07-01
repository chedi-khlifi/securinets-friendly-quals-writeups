# Synthetic Attack Log Generator

## Purpose

This script generates a **synthetic security-event log file** for a blue-team / log-analysis training exercise (SOC/CTF-style challenge). It produces a realistic-looking timeline of a full intrusion — from initial port scanning through to data exfiltration — buried inside a much larger volume of ordinary "noise" logs (normal user logins), so an analyst has to find the needle in the haystack.

## How it works

1. **Attack timeline (`generate_attack_logs`)** — builds a fixed sequence of 21 log lines representing a realistic kill-chain, each offset by a number of minutes from a configurable `ATTACK_START_TIME`.
2. **Noise generation** — uses the `faker` library to generate hundreds of harmless `User login successful` entries with random usernames and private IPs, both *before* and *around* the attack window, so the malicious events don't stand out by position alone.
3. **Merge & sort** — all logs (noise + attack) are concatenated and sorted by timestamp, so the final file reads as one continuous, chronologically ordered event stream.
4. **Output** — everything is written line-by-line to `attack_logs.log`.

## Configuration variables

| Variable | Value | Role |
|---|---|---|
| `ATTACKER_IP` | `10.10.10.55` | Source IP used throughout the attack chain |
| `TARGET_IP` | `10.10.10.14` | Victim host IP |
| `ATTACK_PORT` | `9494` | Port scanned/exploited |
| `MALWARE_NAME` | `chkimbi.exe` | Dropped payload filename |
| `MALWARE_SHA256` | `71a545b7...204527cb` | Hash logged for the dropped file |
| `TARGET_OS` | `caffeslimos` | OS string reported for the victim host |
| `MALWARE_PROCESS` | `ilyes.exe` | Process name once malware executes |
| `ATTACK_START_TIME` | `2025-10-11 10:00:00` | Anchor timestamp; all attack events are offset from this |

Changing these values re-themes the entire scenario (different actor IP, different malware, different challenge) without touching the log-generation logic.

## Attack timeline (kill-chain phases)

| Phase | Offset (min) | Source | Event |
|---|---|---|---|
| 1. Reconnaissance | 0, 2, 4, 6, 8 | Firewall | 5× repeated port-scan warnings from attacker to target |
| 2. Targeted scan | 12 | IDS | Scan narrows to the specific attack port |
| 3. Exploitation attempt | 15–16 | Firewall / IDS | Suspicious connection + potential exploit flagged |
| 4. Connection established | 18 | System | New connection opens on the attack port |
| 5. Malware download | 20–21 | Proxy / Web Filter | File download detected, HTTP GET to attacker payload path |
| 6. File drop | 22–23 | Endpoint | Malware file written to `C:\Windows\Temp\`, hash computed |
| 7. Execution | 25–27 | Endpoint / EDR | Malicious process launches, loads a suspicious DLL, OS fingerprint logged |
| 8. Lateral movement | 30, 32 | Active Directory / EDR | Failed auth attempts, LSASS memory access (credential dumping) |
| 9. Command & Control | 35, 37 | Network / Firewall | Outbound connection to attacker IP, periodic C2 beacon |
| 10. Exfiltration | 40 | DLP | Large outbound data transfer flagged |

This gives the log file a coherent narrative: **scan → exploit → drop → execute → escalate → C2 → exfiltrate** — a fairly standard cyber-kill-chain shape useful for teaching log correlation and timeline reconstruction.

## Volume & noise model

- `total_lines` (default **550**) is the overall size of the generated log file.
- `noise_before_attack` (default **500**) harmless login events are scattered in the 1–3 hours *before* the attack start.
- The remaining budget (`total_lines - attack_logs_count - noise_before_attack` = 550 − 21 − 500 = **29**) is filled with more login noise scattered *during/around* the attack window (0–45 min offset), so attack events sit interleaved with ordinary traffic rather than isolated at the end of the file.
- Final sort by timestamp merges everything into one realistic, chronological log.

With the defaults, this produces **550 total lines**: 21 attack-relevant events hidden among 529 benign login entries (≈3.8% signal-to-noise).

## Output

Running the script calls `save_logs()`, which writes the merged, sorted log lines to `attack_logs.log` in the working directory and prints a confirmation message.

## Suggested exercise use

This kind of generated log is well suited for practicing:
- Timeline reconstruction / kill-chain identification from raw logs
- Filtering signal from noise at scale (grep/regex, SIEM query practice)
- IOC extraction (IPs, hashes, filenames, process names) and MITRE ATT&CK phase mapping
- Building or testing log-parsing/enrichment pipelines (e.g., feeding into a GeoIP/AbuseIPDB/VirusTotal enrichment stage)
