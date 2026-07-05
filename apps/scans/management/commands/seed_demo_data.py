"""
Management command: python manage.py seed_demo_data

Creates a realistic demo dataset:
  - 1 demo user
  - 3 repositories (high/medium/low vulnerability counts)
  - 2 completed scans per repository
  - 40+ realistic findings across all severity levels
  - 30 days of analytics history
"""
from __future__ import annotations

import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data for CodeSentinel."

    def handle(self, *args, **options):
        self.stdout.write("→ Creating demo user...")
        user = self._create_user()

        self.stdout.write("→ Creating repositories...")
        repos = self._create_repos(user)

        self.stdout.write("→ Creating scans and findings...")
        for repo, (finding_count, severity_distribution) in zip(repos, REPO_CONFIGS):
            for scan_offset in [14, 0]:  # Two scans: 14 days ago and today
                scan = self._create_scan(repo, user, scan_offset, finding_count)
                self._create_findings(scan, finding_count, severity_distribution)

        self.stdout.write(self.style.SUCCESS("✓ Demo data seeded successfully."))
        self.stdout.write("  Login: demo@codesentinel.dev / DemoPass123!")

    def _create_user(self):
        user, created = User.objects.get_or_create(
            email="demo@codesentinel.dev",
            defaults={
                "full_name": "Alex Rivera",
                "github_username": "alex-rivera",
                "github_avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
                "is_active": True,
            },
        )
        if created:
            user.set_password("DemoPass123!")
            user.save()
            self.stdout.write(f"  Created user: {user.email}")
        else:
            self.stdout.write(f"  User already exists: {user.email}")
        return user

    def _create_repos(self, user):
        from apps.repositories.models import Repository

        repos = []
        for name, full_name, desc, language in [
            ("MyShop", "alex-rivera/myshop", "Django e-commerce app with high vulnerability density", "Python"),
            ("DataPipeline", "alex-rivera/data-pipeline", "ETL pipeline with medium vulnerability count", "Python"),
            ("UserService", "alex-rivera/user-service", "FastAPI microservice — mostly secure", "Python"),
        ]:
            repo, created = Repository.objects.get_or_create(
                owner=user,
                full_name=full_name,
                defaults={
                    "github_repo_id": random.randint(100000, 999999),
                    "name": name,
                    "github_repo_url": f"https://github.com/{full_name}",
                    "clone_url": f"https://github.com/{full_name}.git",
                    "default_branch": "main",
                    "description": desc,
                    "is_private": False,
                    "language": language,
                    "last_scanned_at": timezone.now(),
                },
            )
            repos.append(repo)
            action = "Created" if created else "Reused"
            self.stdout.write(f"  {action} repo: {full_name}")
        return repos

    def _create_scan(self, repo, user, days_ago: int, finding_count: int):
        from apps.scans.models import Scan, ScanStatus

        started_at = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 12))
        duration = random.uniform(45, 180)  # 45s to 3 minutes

        scan = Scan.objects.create(
            repository=repo,
            triggered_by=user,
            commit_sha="".join(random.choices("0123456789abcdef", k=40)),
            branch="main",
            status=ScanStatus.COMPLETED,
            progress_percent=100,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=duration),
            duration_seconds=duration,
            files_scanned=random.randint(30, 200),
            lines_of_code=random.randint(3000, 25000),
        )

        return scan

    def _create_findings(self, scan, count: int, severity_dist: dict):
        from apps.findings.models import Finding, FindingStatus, Rule

        created = 0
        for severity, num in severity_dist.items():
            for _ in range(num):
                template = random.choice(FINDING_TEMPLATES.get(severity, FINDING_TEMPLATES["medium"]))
                rule = self._get_or_create_rule(template)

                days_since = random.randint(0, 30)
                status = FindingStatus.OPEN
                if random.random() < 0.25:  # 25% resolved
                    status = FindingStatus.RESOLVED

                Finding.objects.create(
                    scan=scan,
                    rule=rule,
                    file_path=random.choice(DEMO_FILE_PATHS),
                    line_start=random.randint(10, 500),
                    line_end=random.randint(10, 520),
                    severity=severity,
                    title=template["title"],
                    description=template["description"],
                    fix_suggestion=template["fix"],
                    code_snippet=template["snippet"],
                    confidence_score=round(random.uniform(0.65, 0.99), 4),
                    source=random.choice(["semgrep", "ml_model", "semgrep"]),
                    owasp_category=template.get("owasp", ""),
                    cwe_id=template.get("cwe", ""),
                    status=status,
                    created_at=timezone.now() - timedelta(days=days_since),
                )
                created += 1

        # Update scan counters
        from django.db.models import Count

        counts = {
            row["severity"]: row["count"]
            for row in scan.findings.values("severity").annotate(count=Count("id"))
        }
        scan.total_findings = sum(counts.values())
        scan.critical_count = counts.get("critical", 0)
        scan.high_count = counts.get("high", 0)
        scan.medium_count = counts.get("medium", 0)
        scan.low_count = counts.get("low", 0)
        scan.info_count = counts.get("info", 0)
        scan.save()
        self.stdout.write(f"  Created {created} findings for scan in {scan.repository.name}")

    def _get_or_create_rule(self, template: dict):
        from apps.findings.models import Rule

        rule, _ = Rule.objects.get_or_create(
            rule_id_slug=template["rule_id"],
            defaults={
                "name": template["title"],
                "description": template["description"],
                "category": template.get("category", "Other"),
                "severity": template.get("severity", "medium"),
                "owasp_category": template.get("owasp", ""),
                "cwe_id": template.get("cwe", ""),
                "language": "python",
            },
        )
        return rule


# ── Configuration ──────────────────────────────────────────────────────────────

# (finding_count, severity_distribution)
REPO_CONFIGS = [
    (52, {"critical": 8, "high": 16, "medium": 18, "low": 10}),   # MyShop — high risk
    (27, {"critical": 2, "high": 8, "medium": 12, "low": 5}),      # DataPipeline — medium risk
    (11, {"critical": 0, "high": 2, "medium": 5, "low": 4}),       # UserService — low risk
]

DEMO_FILE_PATHS = [
    "myshop/views/checkout.py",
    "myshop/models/product.py",
    "myshop/api/auth.py",
    "myshop/utils/db_helper.py",
    "pipeline/extract.py",
    "pipeline/transform.py",
    "pipeline/load.py",
    "service/auth.py",
    "service/users.py",
    "service/api.py",
    "config/settings.py",
    "utils/helpers.py",
]

FINDING_TEMPLATES = {
    "critical": [
        {
            "rule_id": "demo-sql-injection-fstring",
            "title": "SQL Injection via f-string",
            "description": "User input is interpolated directly into an SQL query using an f-string. An attacker can modify the query to extract, modify, or delete arbitrary data.",
            "fix": "Use parameterised queries: cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))",
            "snippet": "cursor.execute(f\"SELECT * FROM products WHERE name = '{name}'\")",
            "category": "SQL Injection",
            "severity": "critical",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-89",
        },
        {
            "rule_id": "demo-command-injection-shell",
            "title": "Command Injection via subprocess shell=True",
            "description": "subprocess.run() with shell=True and a user-controlled command allows arbitrary OS command execution.",
            "fix": "Use subprocess.run(['git', 'clone', repo_url], check=True) without shell=True.",
            "snippet": "subprocess.run(f'git clone {repo_url}', shell=True, check=True)",
            "category": "Command Injection",
            "severity": "critical",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-78",
        },
        {
            "rule_id": "demo-pickle-deserialize",
            "title": "Insecure Deserialization via pickle.loads()",
            "description": "pickle.loads() executes arbitrary Python code embedded in the data stream. Deserializing untrusted data with pickle is equivalent to remote code execution.",
            "fix": "Replace pickle with json.loads() for untrusted data sources.",
            "snippet": "user_prefs = pickle.loads(request.body)",
            "category": "Insecure Deserialization",
            "severity": "critical",
            "owasp": "A08:2021 – Software and Data Integrity Failures",
            "cwe": "CWE-502",
        },
    ],
    "high": [
        {
            "rule_id": "demo-hardcoded-password",
            "title": "Hardcoded Database Password",
            "description": "A database password is hardcoded as a string literal. This credential will be exposed to anyone with read access to the repository.",
            "fix": "Load credentials from environment variables: os.environ['DB_PASSWORD']",
            "snippet": "DB_PASSWORD = 'SuperSecret123!'",
            "category": "Hardcoded Credentials",
            "severity": "high",
            "owasp": "A07:2021 – Identification and Authentication Failures",
            "cwe": "CWE-798",
        },
        {
            "rule_id": "demo-yaml-unsafe-load",
            "title": "Unsafe YAML Deserialization",
            "description": "yaml.load() without Loader=yaml.SafeLoader can execute arbitrary Python objects embedded in YAML.",
            "fix": "Replace yaml.load() with yaml.safe_load().",
            "snippet": "config = yaml.load(config_file)",
            "category": "Insecure Deserialization",
            "severity": "high",
            "owasp": "A08:2021 – Software and Data Integrity Failures",
            "cwe": "CWE-502",
        },
        {
            "rule_id": "demo-eval-injection",
            "title": "Code Injection via eval()",
            "description": "eval() evaluates a user-supplied expression as Python code, allowing arbitrary code execution.",
            "fix": "Use ast.literal_eval() for safe evaluation of literals.",
            "snippet": "result = eval(request.GET.get('expression', ''))",
            "category": "Command Injection",
            "severity": "high",
            "owasp": "A03:2021 – Injection",
            "cwe": "CWE-78",
        },
    ],
    "medium": [
        {
            "rule_id": "demo-md5-password",
            "title": "Weak Hash Function: MD5",
            "description": "MD5 is cryptographically broken and should never be used to hash passwords. Rainbow table attacks can reverse MD5 hashes in seconds.",
            "fix": "Use bcrypt or argon2: from argon2 import PasswordHasher; ph = PasswordHasher(); hash = ph.hash(password)",
            "snippet": "hashed = hashlib.md5(password.encode()).hexdigest()",
            "category": "Cryptography Issues",
            "severity": "medium",
            "owasp": "A02:2021 – Cryptographic Failures",
            "cwe": "CWE-327",
        },
        {
            "rule_id": "demo-random-token",
            "title": "Insecure Random Number Generator",
            "description": "random.random() is not cryptographically secure and must not be used to generate tokens, session IDs, or passwords.",
            "fix": "Use the secrets module: import secrets; token = secrets.token_hex(32)",
            "snippet": "session_token = str(random.random())[2:]",
            "category": "Cryptography Issues",
            "severity": "medium",
            "owasp": "A02:2021 – Cryptographic Failures",
            "cwe": "CWE-338",
        },
        {
            "rule_id": "demo-path-traversal",
            "title": "Potential Path Traversal",
            "description": "A user-controlled value is used in os.path.join() without validation. An attacker can supply '../' sequences to access files outside the intended directory.",
            "fix": "Resolve and validate the path: resolved = Path(base_dir / filename).resolve(); assert str(resolved).startswith(str(base_dir))",
            "snippet": "filepath = os.path.join(UPLOAD_DIR, request.GET.get('filename'))",
            "category": "Path Traversal",
            "severity": "medium",
            "owasp": "A01:2021 – Broken Access Control",
            "cwe": "CWE-22",
        },
    ],
    "low": [
        {
            "rule_id": "demo-bare-except",
            "title": "Bare except Clause Swallows All Exceptions",
            "description": "A bare except: clause catches all exceptions including SystemExit and KeyboardInterrupt, hiding errors and making debugging difficult.",
            "fix": "Catch specific exceptions: except (ValueError, TypeError) as e: logger.error(e)",
            "snippet": "try:\n    process_payment(order)\nexcept:\n    pass",
            "category": "Error Handling",
            "severity": "low",
            "owasp": "",
            "cwe": "",
        },
        {
            "rule_id": "demo-open-no-context",
            "title": "File Opened Without Context Manager",
            "description": "open() is called without a 'with' statement. If an exception occurs, the file handle may not be closed, causing resource leaks.",
            "fix": "Use a context manager: with open(filename) as f: data = f.read()",
            "snippet": "f = open(log_file, 'a')\nf.write(entry)",
            "category": "Resource Management",
            "severity": "low",
            "owasp": "",
            "cwe": "",
        },
    ],
}
