"""
Evaluator — Component V of H = (E, T, C, S, L, V)

Task-type-aware evaluation of worker output before marking tasks 'done'.
Rule-based (default) or LLM intent-check (strict opt-in).
"""

import re
from pathlib import Path
from typing import Tuple, Optional


class TaskType:
    FILE_CREATION = "file_creation"
    TEXT_WRITE = "text_write"
    RESEARCH = "research"
    VAULT_ANALYSIS = "vault_analysis"
    INGESTION = "ingestion"
    COMPLETION_SUMMARY = "completion_summary"  # No artifact expected


class Evaluator:
    def __init__(self, provider_profile: Optional[dict] = None):
        """
        provider_profile: dict with api_key/api_base for strict LLM evaluation.
        If None or missing, strict mode falls back to rule-based.
        """
        self.provider_profile = provider_profile or {}

    # ─────────────────────────────────────────────────────────
    # Task Type Detection
    # ─────────────────────────────────────────────────────────

    def detect_task_type(self, task_body: str) -> Tuple[str, Optional[str]]:
        """
        Returns (task_type, expected_filename_or_None).
        Uses a scoring system to identify the most likely task type.
        """
        body_lower = task_body.lower()
        
        # 1. Scoring based on keyword sets
        scores = {
            TaskType.FILE_CREATION: 0,
            TaskType.TEXT_WRITE: 0,
            TaskType.RESEARCH: 0,
            TaskType.VAULT_ANALYSIS: 0,
            TaskType.INGESTION: 0
        }

        # Keywords mapping
        keywords = {
            TaskType.VAULT_ANALYSIS: ["vault", "notes", "obsidian", "analyze notes", "analyse notes", "second brain"],
            TaskType.RESEARCH: ["research", "analyze", "analyse", "investigate", "report", "review", "evaluate", "survey", "study", "findings", "summarize", "document findings", "compile", "explore"],
            TaskType.INGESTION: ["ingest", "import", "categorize", "classify", "sort", "organize", "tag", "drop folder"],
            TaskType.FILE_CREATION: ["create", "make", "write", "generate", "produce", "build", "output"],
            TaskType.TEXT_WRITE: ["write", "put", "place", "save", "insert"]
        }

        for ttype, kws in keywords.items():
            for kw in kws:
                if kw in body_lower:
                    scores[ttype] += 1

        # 2. Pattern-based detection for filenames
        file_pattern = re.search(r'["\']?(\w[\w\-\.]*\.(?:md|txt|json|py|js|html|csv))["\']?', task_body)
        expected_file = file_pattern.group(1) if file_pattern else None

        explicit_content_phrases = [
            "write exactly",
            "append",
            "containing exactly",
            "contains exactly",
            "with the following content",
            "with content",
        ]
        if expected_file and any(p in body_lower for p in explicit_content_phrases):
            return TaskType.TEXT_WRITE, expected_file

        # 3. Determine best type
        # Prioritize specialty types if they have any score
        if scores[TaskType.VAULT_ANALYSIS] > 0:
            return TaskType.VAULT_ANALYSIS, expected_file or "VAULT_ANALYSIS.md"
        if scores[TaskType.INGESTION] > 0:
            return TaskType.INGESTION, expected_file or "INGESTION_LOG.md"
        if scores[TaskType.RESEARCH] > 0:
            return TaskType.RESEARCH, expected_file

        # Fallback to generic file ops if they have score
        if scores[TaskType.FILE_CREATION] > scores[TaskType.TEXT_WRITE]:
            return TaskType.FILE_CREATION, expected_file
        if scores[TaskType.TEXT_WRITE] > 0:
            return TaskType.TEXT_WRITE, expected_file

        # If we have a file reference but no clear intent keywords, assume creation
        if expected_file:
            return TaskType.FILE_CREATION, expected_file

        return TaskType.COMPLETION_SUMMARY, None

    # ─────────────────────────────────────────────────────────
    # Rule-Based Evaluation (default, zero cost)
    # ─────────────────────────────────────────────────────────

    def evaluate_rule_based(
        self, task_type: str, expected_file: Optional[str], bot_workspace_dir: Path
    ) -> Tuple[bool, str]:
        """
        Fast, zero-cost evaluation. Checks artifact existence and quality/structure.
        """
        # 1. COMPLETION_SUMMARY: check WORKING_NOTES.md for task-specific entry
        if task_type == TaskType.COMPLETION_SUMMARY:
            notes_file = bot_workspace_dir / "WORKING_NOTES.md"
            if not notes_file.exists():
                return False, "completion_summary: WORKING_NOTES.md missing"
            
            content = notes_file.read_text(encoding="utf-8", errors="ignore")
            # Look for recent execution block (very loose check for now)
            if "Brain Execution" in content or "DONE" in content:
                if len(content.strip()) > 1000: # Tightened from 500
                    return True, "completion_summary: WORKING_NOTES.md has execution evidence"
            return False, "completion_summary: No specific evidence of successful execution in notes"

        # 2. Find target file
        target = None
        if expected_file:
            # First check root
            target = bot_workspace_dir / expected_file
            if not target.exists():
                # V4.6 Resilient Search: Check subdirectories (e.g., if harness puts things in a subfolder)
                matches = list(bot_workspace_dir.rglob(expected_file))
                if matches:
                    target = matches[0]
                    print(f"[EVAL] Found '{expected_file}' at '{target.relative_to(bot_workspace_dir)}'")
        else:
            # Multi-artifact scan: find any non-system file with meaningful content
            system_files = {"WORKING_NOTES.md", "ARTIFACTS.md", "TASKS.md", "TEAM_COMMUNICATION.md", "WORKING_NOTES_ARCHIVE.md"}
            allowed_exts = {".md", ".txt", ".json", ".py", ".js", ".html", ".csv"}
            all_files = list(bot_workspace_dir.glob("*"))
            candidates = [
                f for f in all_files
                if f.is_file() and f.name not in system_files and f.suffix in allowed_exts and f.stat().st_size > 50
            ]
            print(f"[EVAL_DEBUG] Scanning {bot_workspace_dir}. Found {len(all_files)} files. Candidates: {[f.name for f in candidates]}")
            if candidates:
                # Sort by mtime to get the freshest one
                candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                target = candidates[0]
                expected_file = target.name
                print(f"[EVAL_DEBUG] Selected freshest candidate: {expected_file}")

        if not target or not target.exists():
            return False, f"evaluation: Expected artifact '{expected_file or 'None'}' missing"

        content = target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""
        content_len = len(content.strip())

        # 3. Type-specific structure and quality checks
        if task_type == TaskType.FILE_CREATION:
            return True, f"file_creation: '{expected_file}' exists"

        elif task_type == TaskType.TEXT_WRITE:
            if content_len < 10:
                return False, f"text_write: '{expected_file}' has trivial content"
            return True, f"text_write: '{expected_file}' updated"

        elif task_type == TaskType.RESEARCH:
            # Accept either markdown section headers or numbered-item structure.
            h1_headers = len(re.findall(r'^#\s', content, re.MULTILINE))
            h2_headers = len(re.findall(r'^##\s', content, re.MULTILINE))
            h3_headers = len(re.findall(r'^###\s', content, re.MULTILINE))
            numbered_items = len(re.findall(r'^\d+\.\s', content, re.MULTILINE))
            bullets = len(re.findall(r'^[-\*]\s', content, re.MULTILINE))
            use_case_markers = len(re.findall(r'^\*\*Use Case:\*\*', content, re.MULTILINE))
            benefit_markers = len(re.findall(r'^\*\*Benefit', content, re.MULTILINE))
            structured_sections = h2_headers + h3_headers + numbered_items
            if content_len < 100:
                return False, f"research: Report too short ({content_len} chars, need 100+)"
            if h1_headers < 1 and structured_sections < 2:
                return False, (
                    f"research: Missing sections (found {h1_headers} H1, {h2_headers} H2, "
                    f"{h3_headers} H3, {numbered_items} numbered items; need title + structure)"
                )
            if h2_headers + h3_headers + numbered_items + bullets + use_case_markers + benefit_markers < 3:
                return False, (
                    f"research: Low detail (found {h2_headers} H2, {h3_headers} H3, "
                    f"{numbered_items} numbered items, {bullets} bullets, "
                    f"{use_case_markers} use-case markers, {benefit_markers} benefit markers; need 3+)"
                )
            return True, "research: Structured report produced"

        elif task_type == TaskType.VAULT_ANALYSIS:
            required = ["## Executive Summary", "## Business Opportunities", "## Source Files"]
            missing = [r for r in required if r not in content]
            if missing:
                return False, f"vault_analysis: Missing sections: {', '.join(missing)}"
            opps = len(re.findall(r'^\d\.\s', content, re.MULTILINE))
            if opps < 3:
                return False, f"vault_analysis: Insufficient opportunities found ({opps}, need 3+)"
            return True, "vault_analysis: Complete structured analysis report produced"

        elif task_type == TaskType.INGESTION:
            if "| " not in content or "---" not in content:
                return False, "ingestion: Missing categorization table"
            rows = len(re.findall(r'^\|', content, re.MULTILINE))
            if rows < 3: # Header + Separator + at least 1 row
                return False, "ingestion: Incomplete ingestion log (no rows in table)"
            return True, "ingestion: Structured audit log produced"

        return True, "evaluation: passed (generic)"

    # ─────────────────────────────────────────────────────────
    # Strict LLM Intent-Check Evaluation (opt-in)
    # ─────────────────────────────────────────────────────────

    def evaluate_strict(
        self,
        task_body: str,
        task_type: str,
        expected_file: Optional[str],
        bot_workspace_dir: Path,
    ) -> Tuple[bool, str]:
        """
        LLM-backed intent verification. Only runs after rule-based passes.
        """
        # Gate: rule-based must pass first
        rule_ok, rule_reason = self.evaluate_rule_based(task_type, expected_file, bot_workspace_dir)
        if not rule_ok:
            return False, f"[strict:rule_failed] {rule_reason}"

        if not self.provider_profile.get("api_key"):
            # No LLM configured — treat rule-based as sufficient
            return rule_ok, f"[strict:no_llm_config] {rule_reason}"

        try:
            from openai import OpenAI
            c_args = {"api_key": self.provider_profile.get("api_key", "none")}
            api_base = self.provider_profile.get("api_base", "")
            if api_base:
                c_args["base_url"] = api_base

            client = OpenAI(**c_args)
            model = self.provider_profile.get("model", "gpt-4o-mini")

            artifact_content = ""
            if expected_file:
                target = bot_workspace_dir / expected_file
                if target.exists():
                    artifact_content = target.read_text(encoding="utf-8", errors="ignore")[:2000]

            check_prompt = (
                f"Task instruction:\n{task_body[:600]}\n\n"
                f"Artifact produced:\n{artifact_content[:1200] if artifact_content else '(no artifact)'}\n\n"
                "Did the artifact satisfy the task instruction? "
                "Respond with exactly: YES - <one-line reason>  OR  NO - <one-line reason>"
            )

            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a strict task evaluator. Be concise."},
                    {"role": "user", "content": check_prompt}
                ],
                max_tokens=120
            )

            answer = (resp.choices[0].message.content or "").strip()
            passed = answer.upper().startswith("YES")
            return passed, f"[strict:llm] {answer}"

        except Exception as e:
            # LLM failure — fall back to rule-based result
            return rule_ok, f"[strict:llm_error:{e}] fallback to rule: {rule_reason}"

    # ─────────────────────────────────────────────────────────
    # Main Entry Point
    # ─────────────────────────────────────────────────────────

    def evaluate(
        self,
        task_id: str,
        task_body: str,
        bot_workspace_dir: Path,
        mode: str = "rule_based"
    ) -> Tuple[bool, str]:
        """
        Main evaluation entry point.
        Returns (passed: bool, reason: str)
        """
        task_type, expected_file = self.detect_task_type(task_body)
        print(
            f"[EVAL] Task {task_id} | Type: {task_type} | "
            f"Expected: {expected_file} | Mode: {mode}"
        )

        if mode == "strict":
            return self.evaluate_strict(task_body, task_type, expected_file, bot_workspace_dir)
        else:
            return self.evaluate_rule_based(task_type, expected_file, bot_workspace_dir)
