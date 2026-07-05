"""
Semgrep runner — wraps the Semgrep CLI and parses its JSON output.
Runs the bundled rules in the /rules directory and returns structured findings.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Map Semgrep severity strings to our canonical severity scale
SEVERITY_MAP = {
    "ERROR": "critical",
    "WARNING": "high",
    "INFO": "medium",
    "LOW": "low",
}

# Default OWASP categories for common rule patterns
OWASP_MAP = {
    "sql-injection": "A03:2021 – Injection",
    "command-injection": "A03:2021 – Injection",
    "hardcoded-credentials": "A07:2021 – Identification and Authentication Failures",
    "insecure-deserialization": "A08:2021 – Software and Data Integrity Failures",
    "crypto-issues": "A02:2021 – Cryptographic Failures",
    "path-traversal": "A01:2021 – Broken Access Control",
    "ssrf": "A10:2021 – Server-Side Request Forgery",
}

CWE_MAP = {
    "sql-injection": "CWE-89",
    "command-injection": "CWE-78",
    "hardcoded-credentials": "CWE-798",
    "insecure-deserialization": "CWE-502",
    "crypto-issues": "CWE-327",
    "path-traversal": "CWE-22",
    "ssrf": "CWE-918",
}


class SemgrepRunner:
    """
    Invoke Semgrep with the bundled rule set and parse the JSON output
    into the canonical finding format expected by the scan task.
    """

    def __init__(self, rules_dir: str | Path | None = None):
        """
        Initialise the runner.

        Args:
            rules_dir: Path to the directory containing .yml rule files.
                       Defaults to the 'rules/' directory relative to the repo root.
        """
        if rules_dir is None:
            # Assume the rules dir lives at the package root
            self.rules_dir = Path(__file__).parent.parent / "rules"
        else:
            self.rules_dir = Path(rules_dir)

    def run(self, target_path: Path) -> list[dict]:
        """
        Run Semgrep against target_path using the bundled rules.

        Returns a list of finding dicts in the canonical format.
        """
        if not self.rules_dir.exists():
            logger.warning("Rules directory not found: %s — skipping Semgrep.", self.rules_dir)
            return []

        cmd = [
            "semgrep",
            "--config", str(self.rules_dir),
            "--json",
            "--quiet",
            "--no-git-ignore",
            str(target_path),
        ]

        logger.info("Running Semgrep: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5-minute timeout
            )
        except subprocess.TimeoutExpired:
            logger.warning("Semgrep timed out after 5 minutes.")
            return []
        except FileNotFoundError:
            logger.warning("Semgrep not found in PATH — skipping static analysis.")
            return []

        if result.returncode not in (0, 1):  # 0 = no findings, 1 = findings found
            logger.warning("Semgrep exited with code %d: %s", result.returncode, result.stderr[:500])
            return []

        if not result.stdout:
            return []

        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            logger.warning("Could not parse Semgrep JSON output: %s", exc)
            return []

        return [self._parse_result(r) for r in raw.get("results", [])]

    def _parse_result(self, result: dict) -> dict:
        """Convert a single Semgrep result into a canonical finding dict."""
        check_id: str = result.get("check_id", "unknown")
        meta: dict = result.get("extra", {}).get("metadata", {})
        message: str = result.get("extra", {}).get("message", "")
        fix: str = result.get("extra", {}).get("fix", "")
        severity_raw: str = result.get("extra", {}).get("severity", "WARNING")

        start: dict = result.get("start", {})
        end: dict = result.get("end", {})

        # Determine category from the rule ID slug
        category = "Other"
        owasp = ""
        cwe = ""
        for pattern, cat in [
            ("sql-injection", "SQL Injection"),
            ("command-injection", "Command Injection"),
            ("hardcoded-credential", "Hardcoded Credentials"),
            ("insecure-deserialization", "Insecure Deserialization"),
            ("deserialization", "Insecure Deserialization"),
            ("crypto", "Cryptography Issues"),
            ("path-traversal", "Path Traversal"),
            ("ssrf", "SSRF"),
        ]:
            if pattern in check_id.lower():
                category = cat
                # Map pattern to OWASP/CWE keys
                base = check_id.lower().split(".")[-1].split("-rule")[0]
                for key in OWASP_MAP:
                    if pattern.startswith(key.split("-")[0]):
                        owasp = OWASP_MAP.get(key, "")
                        cwe = CWE_MAP.get(key, "")
                        break
                break

        return {
            "rule_id": check_id,
            "title": meta.get("title") or _human_title(check_id),
            "description": message or meta.get("description", "A potential security vulnerability was detected."),
            "fix_suggestion": fix or meta.get("fix") or "Review and remediate the flagged code pattern.",
            "file_path": result.get("path", "unknown"),
            "line_start": start.get("line", 1),
            "line_end": end.get("line", start.get("line", 1)),
            "column_start": start.get("col"),
            "column_end": end.get("col"),
            "severity": SEVERITY_MAP.get(severity_raw.upper(), "medium"),
            "category": category,
            "owasp_category": meta.get("owasp") or owasp,
            "cwe_id": meta.get("cwe") or cwe,
            "code_snippet": result.get("extra", {}).get("lines", ""),
            "confidence_score": meta.get("confidence", 0.9),
            "source": "semgrep",
        }


def _human_title(check_id: str) -> str:
    """Convert a dotted rule ID slug to a human-readable title."""
    parts = check_id.split(".")
    last = parts[-1] if parts else check_id
    return " ".join(word.capitalize() for word in last.replace("-", " ").split())
