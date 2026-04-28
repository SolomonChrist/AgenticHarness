#!/usr/bin/env python3
"""Self-test for the Telegram-first ChiefChat path."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import ChiefChat.chief_chat_service as service
from ChiefChat.chief_chat_service import (
    apply_voice_cleanup,
    broad_location_clarification,
    evidence_fallback_reply,
    extract_weather_location,
    is_model_identity_request,
    is_presence_ping,
    looks_like_progress_reply,
    plan_web_search_query,
    requested_route_roles,
    resolved_chat_model,
    run_once,
    violates_chief_voice,
    weather_code_label,
)
from chat_ledger import parse_chat_records
from operator_messaging import append_operator_message


TEMP_DIRS: list[tempfile.TemporaryDirectory] = []


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_root() -> Path:
    temp = tempfile.TemporaryDirectory()
    TEMP_DIRS.append(temp)
    root = Path(temp.name)
    write(root / "AGENTIC_HARNESS.md", "# Agentic Harness\n")
    write(root / "HUMANS.md", "ID: TestHuman\n")
    write(root / "LAYER_LAST_ITEMS_DONE.md", "# Events\n")
    write(root / "LAYER_TASK_LIST.md", "# Tasks\n")
    write(root / "MEMORY" / "agents" / "Chief_of_Staff" / "SOUL.md", "Be warm, concise, and operational.\n")
    write(root / "MEMORY" / "agents" / "Chief_of_Staff" / "ALWAYS.md", "Remember this is a test harness.\n")
    write(
        root / "Runner" / "ROLE_LAUNCH_REGISTRY.md",
        "\n".join(
            [
                "### ROLE",
                "Role: Chief_of_Staff",
                "Enabled: YES",
                "Automation Ready: YES",
                "Harness Type: cheap-chief",
                "Model / Profile: fake",
                "",
                "### ROLE",
                "Role: Engineer",
                "Enabled: YES",
                "Automation Ready: YES",
                "Harness Type: Claude Code",
                "Model / Profile: claude-haiku-test",
                "",
                "### ROLE",
                "Role: Researcher",
                "Enabled: YES",
                "Automation Ready: NO",
                "Harness Type: Claude Code",
                "Model / Profile: claude-haiku-test",
            ]
        ),
    )
    write(root / "Runner" / ".runner_state.json", json.dumps({"roles": {"Chief_of_Staff": {"provider_cooldown_until": "2999-01-01T00:00:00-05:00"}}}))
    write(
        root / "ChiefChat" / "CHIEF_CHAT_CONFIG.md",
        "\n".join(
            [
                "Chat Provider: fake",
                "Chat Model: fake",
                "Browser Enabled: NO",
                "Max Messages Per Pass: 5",
            ]
        ),
    )
    return root


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: expected {needle!r} in {text!r}")


def main() -> int:
    if extract_weather_location("Check the weather in Toronto") != "Toronto":
        raise AssertionError("expected weather location extraction for Toronto")
    if extract_weather_location("What's the weather for Mississauga right now?") != "Mississauga":
        raise AssertionError("expected weather location extraction for Mississauga")
    if not broad_location_clarification("California"):
        raise AssertionError("expected broad California weather clarification")
    if weather_code_label(2) != "partly cloudy":
        raise AssertionError("expected WMO weather code mapping")
    if not is_model_identity_request("What AI model are you running on?"):
        raise AssertionError("expected model identity request detection")
    if not is_presence_ping("Hello are you available again?"):
        raise AssertionError("expected presence ping detection")
    query_cases = {
        "Ok can you research events coming up in Toronto?": "upcoming events Toronto this week",
        "What tech meetups and events are happening in downtown Toronto tonight?": "tech meetups and events Downtown Toronto tonight",
        "Can you tell me what coffee shops are near me? I'm in etobicoke right now": "best coffee shops Etobicoke reviews",
        "What's the cheapest gas price near me right now? I'm in Mississauga": "cheapest gas prices Mississauga GasBuddy",
        "Can you research the github repo for ABC github and then send me a summary of what it does?": "ABC GitHub repository",
    }
    for request, expected in query_cases.items():
        actual = plan_web_search_query(request)
        if actual != expected:
            raise AssertionError(f"expected planned query {expected!r}, got {actual!r}")

    original_http_get_json = service.http_get_json
    original_http_json = service.http_json
    try:
        service.http_get_json = lambda url, timeout: {"data": [{"id": "gemma-test-model"}]}

        def fake_http_json(url: str, payload: dict, timeout: int) -> dict:
            if payload.get("model") != "gemma-test-model":
                raise AssertionError(f"expected resolved model id, got {payload.get('model')!r}")
            return {"choices": [{"message": {"content": "resolved ok"}}]}

        service.http_json = fake_http_json
        config = {
            "Chat Provider": "openai-compatible",
            "Chat Model": "local-model-name",
            "OpenAI Compatible Base URL": "http://127.0.0.1:1234/v1",
        }
        if resolved_chat_model(config) != "gemma-test-model":
            raise AssertionError("expected placeholder chat model to resolve from /models")
        if service.openai_compatible_reply(config, "hello") != "resolved ok":
            raise AssertionError("expected OpenAI-compatible reply to use resolved model id")
    finally:
        service.http_get_json = original_http_get_json
        service.http_json = original_http_json

    note = "\n".join(
        [
            "Web research completed.",
            "1. Example Source",
            "URL: https://example.com",
            "Evidence:",
            "- Example evidence with a useful number 123 and enough detail to answer.",
        ]
    )
    fallback = evidence_fallback_reply(note, "TASK-WEB-TEST")
    assert_contains(fallback, "Example Source", "web fallback source")
    if not looks_like_progress_reply("Hey! I'm checking that now.", note):
        raise AssertionError("expected progress-only web reply to be rejected")
    if not violates_chief_voice("Understood, Solomon. I will ensure this is handled."):
        raise AssertionError("expected robotic voice phrase to be rejected")
    assert_contains(apply_voice_cleanup("Understood, Solomon. I will ensure this is handled."), "Got it", "voice cleanup")

    root = make_root()
    routed_roles = requested_route_roles(
        root,
        "Send these notes over to both engineer and researcher for the n8n training plan.",
    )
    if routed_roles != ["Engineer", "Researcher"]:
        raise AssertionError(f"expected Engineer and Researcher routing, got {routed_roles!r}")

    append_operator_message(root, "Hi", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed message, got {processed}")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "I am here", "telegram-style reply")
    records = parse_chat_records(root)
    if not any(record.get("direction") == "chief_to_operator" for record in records):
        raise AssertionError("expected Chief reply in chat ledger")

    append_operator_message(root, "Hello are you available again?", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed presence ping, got {processed}")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "I am here and connected", "presence ping reply")

    append_operator_message(root, "Look up the latest status of example.com", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed web message, got {processed}")
    tasks = (root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    assert_contains(tasks, "TASK-WEB-", "web task creation")
    assert_contains(tasks, "Browser automation is disabled", "browser fallback note")

    append_operator_message(root, "What AI model are you running on?", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed identity message, got {processed}")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "ChiefChat", "identity reply names ChiefChat")
    if "claude-haiku-test" in outbox.split("ChiefChat")[-1].split("##", 1)[0] and "Separate deep-work" not in outbox:
        raise AssertionError("identity reply must distinguish chat model from deep-work model")

    append_operator_message(
        root,
        "I need to design a full n8n training program. Send these notes over to both engineer and researcher.",
        source="telegram",
        human_id="TestHuman",
    )
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed routing message, got {processed}")
    tasks = (root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    wakes = (root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    assert_contains(tasks, "TASK-CHIEFCHAT-ENGINEER", "engineer routed task")
    assert_contains(tasks, "TASK-CHIEFCHAT-RESEARCHER", "researcher routed task")
    assert_contains(wakes, "Engineer: routed_task", "engineer wake request")
    assert_contains(wakes, "Researcher: routed_task", "researcher wake request")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "Researcher is queued, but needs a confirmed harness", "not-ready routing honesty")

    append_operator_message(root, "What is the weather today in California", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed ambiguous weather message, got {processed}")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "California the state", "ambiguous location clarification")
    print("CHIEF CHAT SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
