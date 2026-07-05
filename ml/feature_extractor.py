"""
AST-based feature extractor.

Extracts 50 hand-crafted binary/integer features from Python source files
using the Tree-sitter parser. These features are designed to capture common
vulnerability patterns and are combined with CodeBERT embeddings in the ML pipeline.
"""
from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# ── Feature definitions ───────────────────────────────────────────────────────
# Each feature is a (name, description) tuple — used for documentation
# and model training introspection.
FEATURE_NAMES = [
    "has_sql_string_format",          # f"SELECT * FROM {table}"
    "has_exec_eval",                  # exec() or eval() calls
    "has_subprocess_shell_true",      # subprocess.run(shell=True)
    "has_pickle_load",                # pickle.loads() — deserialization
    "has_yaml_load_unsafe",           # yaml.load() without Loader=SafeLoader
    "has_hardcoded_password",         # password = "literal"
    "has_md5_sha1_usage",             # hashlib.md5() / hashlib.sha1()
    "has_random_not_secrets",         # random.random() for token generation
    "has_bare_except",                # bare except: clause
    "has_assert_as_security_guard",   # assert used for auth checks
    "has_request_user_input_direct",  # direct OS command from user input
    "has_open_without_context",       # open() outside with statement
    "has_infinite_loop_pattern",      # while True without break
    "sql_query_string_concat",        # "SELECT" + variable concatenation
    "uses_os_system",                 # os.system() calls
    "uses_os_popen",                  # os.popen() calls
    "uses_tempfile_insecure",         # tempfile.mktemp() (insecure)
    "has_global_keyword",             # global variable mutations
    "has_dangerous_import",           # import ctypes/cffi/winreg
    "has_unvalidated_redirect",       # redirect(request.GET.get("next"))
    "has_path_join_user_input",       # os.path.join() with user input
    "has_requests_user_url",          # requests.get(user_controlled_url)
    "has_jwt_decode_no_verify",       # jwt.decode(..., verify=False)
    "has_debug_mode_enabled",         # DEBUG = True in code
    "has_insecure_hash_password",     # pbkdf2 / bcrypt absence signal
    "has_string_format_in_sql",       # .format() on SQL strings
    "has_percent_format_in_sql",      # "SELECT %s" % user_value
    "has_ssrf_pattern",               # urllib.request with variable URL
    "has_ldap_injection",             # LDAP filter with user input
    "has_xml_external_entity",        # xml.etree parsing user content
    "uses_marshal_loads",             # marshal.loads() — unsafe
    "has_logging_sensitive_data",     # logging.info(password)
    "has_weak_random_seed",           # random.seed() with static value
    "has_cors_allow_all",             # Access-Control-Allow-Origin: *
    "has_sql_execute_with_format",    # cursor.execute(f"…")
    "line_count",                     # Number of lines in function (normalized)
    "import_count",                   # Number of imports (complexity signal)
    "try_except_count",               # Number of try/except blocks
    "function_call_count",            # Total function calls (complexity)
    "string_literal_count",           # Number of string literals
    "has_null_check_absent",          # Missing None checks before attribute access
    "has_type_confusion",             # isinstance() checks absent on user input
    "has_race_condition_pattern",     # Non-atomic check-then-act patterns
    "has_cryptography_misuse",        # ECB mode, no IV, etc.
    "has_timing_attack_risk",         # == comparison of secrets/tokens
    "has_infinite_recursion_risk",    # Self-referential recursive calls
    "has_command_in_string",          # Shell command-like string literals
    "has_cleartext_storage",          # Password/key written to plaintext file
    "has_unescaped_output",           # print(user_input) without sanitisation
    "has_path_traversal_risk",        # "../" in path construction
]

assert len(FEATURE_NAMES) == 50, f"Expected 50 features, got {len(FEATURE_NAMES)}"


class FeatureExtractor:
    """
    Extract the 50 AST features from a list of Python source files.
    Returns code blocks (functions/methods) with their feature vectors.
    """

    def extract_from_files(self, files: list[Path]) -> list[dict]:
        """
        Process each file and return a list of code block dicts:
        {
            "file_path": str,
            "line_start": int,
            "line_end": int,
            "code": str,
            "ast_features": np.ndarray  # shape (50,)
        }
        """
        blocks = []
        for path in files:
            try:
                source = path.read_text(encoding="utf-8", errors="ignore")
                file_blocks = self._extract_blocks(str(path), source)
                blocks.extend(file_blocks)
            except Exception as exc:
                logger.debug("Skipped %s: %s", path, exc)
        return blocks

    def _extract_blocks(self, file_path: str, source: str) -> list[dict]:
        """Split a source file into function-level blocks and extract features."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Treat the whole file as one block if it can't be parsed
            return [self._make_block(file_path, source, 1, source.count("\n") + 1)]

        blocks = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    start = node.lineno
                    end = node.end_lineno or (start + 20)
                    lines = source.splitlines()
                    code = "\n".join(lines[start - 1 : end])
                    if len(code.strip()) < 10:
                        continue
                    blocks.append(self._make_block(file_path, code, start, end))
                except Exception:
                    continue

        if not blocks:
            # No functions — treat the whole file as one block
            blocks.append(self._make_block(file_path, source[:8000], 1, source.count("\n") + 1))

        return blocks

    def _make_block(self, file_path: str, code: str, line_start: int, line_end: int) -> dict:
        """Create a block dict with extracted AST features."""
        return {
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "code": code,
            "ast_features": self._extract_features(code),
        }

    def _extract_features(self, code: str) -> np.ndarray:
        """Return a 50-dimensional binary/integer feature vector for the given code."""
        features = np.zeros(50, dtype=np.float32)

        c = code  # alias for brevity

        features[0]  = 1.0 if re.search(r'f["\'].*SELECT|INSERT|UPDATE|DELETE', c, re.I) else 0.0
        features[1]  = 1.0 if re.search(r'\b(exec|eval)\s*\(', c) else 0.0
        features[2]  = 1.0 if re.search(r'subprocess\.(run|Popen|call).*shell\s*=\s*True', c, re.S) else 0.0
        features[3]  = 1.0 if re.search(r'pickle\.(loads?|Unpickler)', c) else 0.0
        features[4]  = 1.0 if re.search(r'yaml\.load\s*\([^)]+\)', c) and 'SafeLoader' not in c else 0.0
        features[5]  = 1.0 if re.search(r'(password|passwd|secret|api_key|token)\s*=\s*["\'][^"\']{4,}', c, re.I) else 0.0
        features[6]  = 1.0 if re.search(r'hashlib\.(md5|sha1)\s*\(', c) else 0.0
        features[7]  = 1.0 if re.search(r'\brandom\.(random|randint|choice|shuffle)\s*\(', c) else 0.0
        features[8]  = 1.0 if re.search(r'\bexcept\s*:', c) else 0.0
        features[9]  = 1.0 if re.search(r'\bassert\b.*(auth|permission|admin|role|login|user)', c, re.I) else 0.0
        features[10] = 1.0 if re.search(r'os\.(system|popen)\s*\(.*input|request|argv', c, re.S) else 0.0
        features[11] = 1.0 if re.search(r'\bopen\s*\([^)]+\)', c) and 'with open' not in c else 0.0
        features[12] = 1.0 if re.search(r'while\s+True', c) and 'break' not in c else 0.0
        features[13] = 1.0 if re.search(r'"(SELECT|INSERT|UPDATE|DELETE)[^"]*"\s*\+', c, re.I) else 0.0
        features[14] = 1.0 if re.search(r'\bos\.system\s*\(', c) else 0.0
        features[15] = 1.0 if re.search(r'\bos\.popen\s*\(', c) else 0.0
        features[16] = 1.0 if re.search(r'\btempfile\.mktemp\s*\(', c) else 0.0
        features[17] = min(len(re.findall(r'\bglobal\b', c)), 5) / 5.0
        features[18] = 1.0 if re.search(r'\bimport\s+(ctypes|cffi|winreg|_winapi)', c) else 0.0
        features[19] = 1.0 if re.search(r'redirect\s*\(.*request\.(GET|POST)', c) else 0.0
        features[20] = 1.0 if re.search(r'os\.path\.join\s*\(.*request|input|argv', c, re.S) else 0.0
        features[21] = 1.0 if re.search(r'requests\.(get|post)\s*\([^)]*request\.(GET|POST|args)', c, re.S) else 0.0
        features[22] = 1.0 if re.search(r'jwt\.decode\s*\([^)]*verify\s*=\s*False', c) else 0.0
        features[23] = 1.0 if re.search(r'\bDEBUG\s*=\s*True', c) else 0.0
        features[24] = 0.0  # placeholder for hash strength signal
        features[25] = 1.0 if re.search(r'"[^"]*SELECT[^"]*"\.format\s*\(', c, re.I) else 0.0
        features[26] = 1.0 if re.search(r'"[^"]*SELECT[^"]*"\s*%\s', c, re.I) else 0.0
        features[27] = 1.0 if re.search(r'urllib\.request\.(urlopen|urlretrieve)\s*\(', c) else 0.0
        features[28] = 1.0 if re.search(r'ldap.*search.*request|input', c, re.S) else 0.0
        features[29] = 1.0 if re.search(r'xml\.etree.*parse|fromstring', c) else 0.0
        features[30] = 1.0 if re.search(r'\bmarshal\.loads?\s*\(', c) else 0.0
        features[31] = 1.0 if re.search(r'\blogging\.(debug|info|warning)\s*\([^)]*password|secret|token', c, re.I) else 0.0
        features[32] = 1.0 if re.search(r'random\.seed\s*\(\s*\d+\s*\)', c) else 0.0
        features[33] = 1.0 if re.search(r'Access-Control-Allow-Origin.*\*', c) else 0.0
        features[34] = 1.0 if re.search(r'cursor\.execute\s*\(.*f["\']', c, re.S) else 0.0
        # Numeric features (normalised)
        line_count = c.count("\n") + 1
        features[35] = min(line_count / 200.0, 1.0)
        features[36] = min(len(re.findall(r'\bimport\b', c)) / 10.0, 1.0)
        features[37] = min(len(re.findall(r'\btry\b', c)) / 5.0, 1.0)
        features[38] = min(len(re.findall(r'\w+\s*\(', c)) / 50.0, 1.0)
        features[39] = min(len(re.findall(r'["\'][^"\']{2,}["\']', c)) / 20.0, 1.0)
        features[40] = 1.0 if re.search(r'\.\w+\s*(?!\s*=)(?!\s*\()(?=\s)', c) else 0.0
        features[41] = 1.0 if re.search(r'isinstance\s*\(' , c) else 0.0
        features[42] = 1.0 if re.search(r'if\s+.+:\s*\n\s*(open|os\.system|subprocess)', c) else 0.0
        features[43] = 1.0 if re.search(r'AES\.MODE_ECB|Cipher\(.+ECB', c) else 0.0
        features[44] = 1.0 if re.search(r'(secret|token|password)\s*==\s*', c, re.I) else 0.0
        features[45] = 0.0  # placeholder
        features[46] = 1.0 if re.search(r'(os\.system|subprocess)\s*\(\s*["\'][^"\']+["\']', c) else 0.0
        features[47] = 1.0 if re.search(r'open\s*\(.+["\'][wa]["\']', c) and re.search(r'password|secret|key', c, re.I) else 0.0
        features[48] = 1.0 if re.search(r'\bprint\s*\(.*request\.(GET|POST|args)', c) else 0.0
        features[49] = 1.0 if re.search(r'["\']\.\./', c) else 0.0

        return features
