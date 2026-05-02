#!/usr/bin/env python3
"""Self-test for the Telegram-first ChiefChat path."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import ChiefChat.chief_chat_service as service
from ChiefChat.chief_chat_service import (
    apply_voice_cleanup,
    activity_path,
    actionable_task_count,
    broad_location_clarification,
    build_prompt,
    cancel_stale_web_tasks,
    detect_operator_intent,
    evidence_fallback_reply,
    extract_today_checklist_items,
    extract_location_hint,
    extract_numbered_tasks,
    extract_role_add_request,
    extract_weather_location,
    extract_human_assist_request,
    is_model_identity_request,
    is_bad_search_result,
    is_presence_ping,
    is_situational_location_request,
    is_single_task_capture_request,
    is_skill_note_request,
    is_role_takeover_request,
    is_task_intake_request,
    is_task_action_request,
    is_today_checklist_request,
    is_role_wake_request,
    is_work_request,
    is_web_request,
    is_automation_hostile_url,
    lacks_web_answer_evidence,
    looks_like_access_block,
    looks_like_progress_reply,
    plan_web_search_queries,
    plan_web_search_query,
    recommend_task_roles,
    requested_route_roles,
    resolved_chat_model,
    role_alias_map,
    role_skill_file,
    run_once,
    situational_evidence_reply,
    violates_chief_voice,
    web_source_cards,
    weather_code_label,
)
from chat_ledger import parse_chat_records
from message_filters import telegram_plain_text
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
    write(root / "MEMORY" / "humans" / "TestHuman" / "ALWAYS.md", "Mary is an important named person in the operator's life and should not be forgotten.\n")
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
    intake_text = "\n".join(
        [
            "Add these tasks to the list of tasks that we need to get done and figure out which team members we need:",
            "1. Create a full course outline for the Introduction to Claude course.",
            "2. Research and implement the fastest workflow for creating course videos.",
            "3. Build a simple KPI update system with spreadsheets and dashboards.",
        ]
    )
    if len(extract_numbered_tasks(intake_text)) != 3:
        raise AssertionError("expected numbered task extraction")
    if not is_task_intake_request(intake_text):
        raise AssertionError("expected task intake detection")
    if is_web_request(intake_text):
        raise AssertionError("task intake must not be treated as a web request")
    owner, support = recommend_task_roles("Build a simple KPI update system with spreadsheets and dashboards.")
    if owner != "Engineer" or "Engineer" not in support:
        raise AssertionError("expected KPI system to route to Engineer")
    if extract_role_add_request("Yes add the strategist role please") != "Strategist":
        raise AssertionError("expected role-add extraction for Strategist")
    human_name, _human_request = extract_human_assist_request("Ask Mary to help you with obsidian")
    if human_name != "Mary":
        raise AssertionError("expected named-human assist extraction for Mary")
    human_name, _human_request = extract_human_assist_request("Can you check with Mary on my latest lead list")
    if human_name != "Mary":
        raise AssertionError("expected check-with named-human assist extraction for Mary")
    human_name, _human_request = extract_human_assist_request("Go check again, no don't use tools you have access to the system. Make note of this error")
    if human_name:
        raise AssertionError(f"did not expect generic word to be captured as human name, got {human_name!r}")
    if not is_single_task_capture_request("Go check again, no don't use tools you have access to the system. Make note of this error"):
        raise AssertionError("expected bug/error note to be captured as single task")
    work_text = "I need you to go through my list of leads and prepare a message for my marketing team member."
    if not is_work_request(work_text):
        raise AssertionError("expected freeform work request detection")
    friend_text = "Today was a lot, and I just need to talk through what to do next."
    if is_web_request(friend_text):
        raise AssertionError("normal human conversation with 'today' must not trigger web search")
    day_text = (
        "Make note of my current tasks for today one I have to go pick up the mango and roti from Leelas Roti Shop "
        "to. I have to grab food for everyone from Chick-fil-A three I have to drop the mango over to uncle Vishnu "
        "and get out fast for I have to get back to the house and help out."
    )
    day_items = extract_today_checklist_items(day_text)
    if len(day_items) != 4:
        raise AssertionError(f"expected 4 spoken day checklist items, got {day_items!r}")
    if not is_today_checklist_request(day_text):
        raise AssertionError("expected personal day checklist detection")
    if "Researcher" in day_items[0]:
        raise AssertionError("personal day checklist must not route through Researcher extraction")
    formatted = telegram_plain_text("*   **Yelp Search:** [Top lunch](https://example.com)\n`TASK-1` Chick·fil·A")
    if "**" in formatted or "[" in formatted or "](" in formatted or "·" in formatted:
        raise AssertionError(f"expected Telegram plain-text cleanup, got {formatted!r}")
    if "Top lunch: https://example.com" not in formatted or "Chick-fil-A" not in formatted:
        raise AssertionError(f"expected Telegram link/brand cleanup, got {formatted!r}")
    lineup_request = "I'm right now on Bloor and Bathurst in Toronto and there's a big line by a movie theatre. What's going on?"
    if extract_location_hint(lineup_request) != "Bloor and Bathurst Toronto":
        raise AssertionError("expected Bloor/Bathurst location extraction")
    if not is_situational_location_request(lineup_request):
        raise AssertionError("expected situational lineup request detection")
    if plan_web_search_query(lineup_request) != "Bloor and Bathurst Toronto lineup event today":
        raise AssertionError("expected situational query planning")
    fanout = plan_web_search_queries("Use the search to see what events are going on at the bl ooor Bathurst area right now in Toronto")
    if "Hot Docs Ted Rogers Cinema schedule today" not in fanout:
        raise AssertionError(f"expected Hot Docs fan-out query, got {fanout!r}")
    if is_bad_search_result({"title": "What's on going or whats on go?", "url": "https://textranch.com/c/whats-on-going", "snippet": "grammar"}, "Bloor Bathurst Toronto", lineup_request) is not True:
        raise AssertionError("expected grammar source filtering")
    if is_bad_search_result({"title": "Events in Bathurst New Brunswick", "url": "https://example.com", "snippet": "Bathurst, New Brunswick"}, "Bloor Bathurst Toronto", lineup_request) is not True:
        raise AssertionError("expected wrong Bathurst location filtering")
    query_cases = {
        "Ok can you research events coming up in Toronto?": "upcoming events Toronto this week",
        "What tech meetups and events are happening in downtown Toronto tonight?": "tech meetups and events Downtown Toronto tonight",
        "Can you tell me what coffee shops are near me? I'm in etobicoke right now": "best coffee shops Etobicoke reviews",
        "What's the cheapest gas price near me right now? I'm in Mississauga": "cheapest gas prices Mississauga GasBuddy",
        "Can you research the github repo for ABC github and then send me a summary of what it does?": "ABC GitHub repository",
        "Find me Congee Queen Mississauga's phone number": "Congee Queen Mississauga official phone number",
        "What can we buy at Chick-fil-A? That will feed five grown people fully so they don't feel hungry afterwards.": "Chick-fil-A Canada menu catering group meal prices official",
    }
    for request, expected in query_cases.items():
        actual = plan_web_search_query(request)
        if actual != expected:
            raise AssertionError(f"expected planned query {expected!r}, got {actual!r}")
    if not is_web_request("Find me Congee Queen Mississauga's phone number"):
        raise AssertionError("expected business phone lookup to use web path")
    if not is_web_request("What can we buy at Chick-fil-A? That will feed five grown people fully."):
        raise AssertionError("expected Chick-fil-A group order to use web/food path")
    if not is_automation_hostile_url("https://www.yelp.ca/search?find_desc=Lunch&find_loc=Brampton,+ON"):
        raise AssertionError("expected Yelp to be treated as automation-hostile")
    if not is_automation_hostile_url("https://www.tripadvisor.com/Restaurants-g154982-zfp30-Brampton_Ontario.html"):
        raise AssertionError("expected Tripadvisor to be treated as automation-hostile")
    if is_automation_hostile_url("https://www.example.com/restaurants"):
        raise AssertionError("expected normal source to stay readable")
    if not looks_like_access_block("Tripadvisor\nAccess is temporarily restricted\nWe detected unusual activity from your device or network."):
        raise AssertionError("expected access-block detection")

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
    cards = web_source_cards(note)
    if not cards or cards[0].get("title") != "Example Source":
        raise AssertionError(f"expected source-card extraction, got {cards!r}")
    event_fallback = evidence_fallback_reply(
        "\n".join(
            [
                "Original operator request: What tech meetups are happening in Toronto tonight?",
                "Web research completed.",
                "1. Tech Social Toronto",
                "URL: https://techsocialtoronto.com/",
                "Snippet: Weekly networking events for developers and data professionals.",
                "2. Eventbrite Toronto Tech Events",
                "URL: https://www.eventbrite.ca/",
                "Snippet: Technology events happening today in Toronto.",
            ]
        ),
        "TASK-WEB-EVENTS",
        "What tech meetups are happening in Toronto tonight?",
    )
    assert_contains(event_fallback, "Tech Social Toronto", "event fallback concrete source")
    blocked_fallback = evidence_fallback_reply(
        "\n".join(
            [
                "Web research completed.",
                "Search results:",
                "1. Yelp Best Lunch Brampton",
                "URL: https://www.yelp.ca/search?find_desc=Lunch&find_loc=Brampton,+ON",
                "2. Official Brampton Food Guide",
                "URL: https://example.com/brampton-food",
                "Snippet: Official local food listings.",
                "Opened sources:",
                "1. Skipped automated read",
                "URL: https://www.yelp.ca/search?find_desc=Lunch&find_loc=Brampton,+ON",
                "Automation note: Skipped automated read: source commonly blocks automation.",
                "2. Official Brampton Food Guide",
                "URL: https://example.com/brampton-food",
                "Evidence:",
                "- Official local food listings with lunch options.",
            ]
        ),
        "TASK-WEB-BLOCKED",
        "Find me lunch in Brampton",
    )
    assert_contains(blocked_fallback, "blocked automated access", "blocked source fallback")
    assert_contains(blocked_fallback, "Official Brampton Food Guide", "blocked fallback usable source")
    group_order = evidence_fallback_reply(
        "Web research completed.\n1. Chick-fil-A Canada Menu\nURL: https://www.chick-fil-a.ca/menu",
        "TASK-WEB-FOOD",
        "What can we buy at Chick-fil-A? That will feed five grown people fully.",
    )
    assert_contains(group_order, "30-count nuggets", "group food fallback")
    assert_contains(group_order, "five sandwiches", "group food quantities")
    if not lacks_web_answer_evidence("I'm checking on that for you now.", note, "What tech events are happening tonight?"):
        raise AssertionError("expected weak web answer to fail evidence quality gate")
    hot_docs_note = "\n".join(
        [
            "Original operator request: I am at Bloor and Bathurst and there is a big lineup near a movie theatre.",
            "Situational investigation mode: lineup/crowd/current-place request.",
            "Search results:",
            "1. Amy Goodman In-Person for Hot Docs Big Ideas screening of Steal This Story, Please!",
            "URL: https://www.democracynow.org/events/2026/4/amy_goodman_inperson_for_hot_docs_big_ideas_screening_of_steal_this_story_please_1623",
            "Evidence:",
            "- Amy Goodman will appear in-person at Hot Docs for the screening of Steal This Story, Please! and for the post-screening discussion, joined by Tia Lessin.",
            "- 5:00 PM: Big Ideas Cocktail. 6:30 PM: Big Ideas Screening & Discussion.",
            "- Journalist Amy Goodman joins Oscar-nominated filmmaker Tia Lessin for a conversation about independent journalism.",
        ]
    )
    hot_docs_reply = situational_evidence_reply(hot_docs_note, "TASK-WEB-HOTDOCS")
    assert_contains(hot_docs_reply, "likely reason", "situational friend-style answer")
    assert_contains(hot_docs_reply, "Amy Goodman", "situational event guest")
    assert_contains(hot_docs_reply, "6:30 PM", "situational event time")
    assert_contains(hot_docs_reply, "Confidence: high", "situational confidence")
    if not looks_like_progress_reply("Hey! I'm checking that now.", note):
        raise AssertionError("expected progress-only web reply to be rejected")
    if not violates_chief_voice("Understood, operator. I will ensure this is handled."):
        raise AssertionError("expected robotic voice phrase to be rejected")
    assert_contains(apply_voice_cleanup("Understood, operator. I will ensure this is handled."), "Got it", "voice cleanup")

    root = make_root()
    prompt = build_prompt(
        root,
        service.load_config(root),
        {"id": "TEST", "body": "What happened to Mary?"},
    )
    assert_contains(prompt, "Mary is an important named person", "active human memory context")
    intent, _reason = detect_operator_intent(root, friend_text)
    if intent != "chat":
        raise AssertionError(f"expected friend message to be chat intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "What tech meetups are happening in Toronto tonight?")
    if intent != "web":
        raise AssertionError(f"expected events message to be web intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, day_text)
    if intent != "today_checklist":
        raise AssertionError(f"expected day checklist intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "Can you find me the hours for Eaton Centre in Toronto?")
    if intent != "web":
        raise AssertionError(f"expected hours lookup to be web intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, intake_text)
    if intent != "task_intake":
        raise AssertionError(f"expected backlog list to be task_intake intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "Yes add the strategist role please")
    if intent != "role_add":
        raise AssertionError(f"expected role-add intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "Status update")
    if intent != "status":
        raise AssertionError(f"expected status intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "Ask Mary to help you with obsidian")
    if intent != "human_assist":
        raise AssertionError(f"expected human-assist intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "Can you check with Mary on my latest lead list")
    if intent != "human_assist":
        raise AssertionError(f"expected check-with human-assist intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, "Go check again, no don't use tools you have access to the system. Make note of this error")
    if intent != "single_task_capture":
        raise AssertionError(f"expected bug note task capture intent, got {intent!r}")
    intent, _reason = detect_operator_intent(root, work_text)
    if intent != "work_request":
        raise AssertionError(f"expected work-request intent, got {intent!r}")

    bot_root = make_root()
    write(
        bot_root / "ROLES.md",
        "\n".join(
            [
                "## Role",
                "Name: Knowledge Architect",
                "Lease File: `_heartbeat/Knowledge_Architect.md`",
                "Direct Message File: `_messages/Knowledge_Architect.md`",
            ]
        ),
    )
    write(
        bot_root / "_heartbeat" / "Knowledge_Architect.md",
        "\n".join(
            [
                "# Knowledge Architect - Mary",
                "**Role**: Knowledge Architect",
                "**Name**: Mary",
                "**Status**: ACTIVE",
            ]
        ),
    )
    aliases = role_alias_map(bot_root)
    if aliases.get("mary") != "Knowledge_Architect":
        raise AssertionError(f"expected Mary alias to resolve to Knowledge_Architect, got {aliases.get('mary')!r}")
    intent, reason = detect_operator_intent(bot_root, "Can you check with Mary on my latest lead list")
    if intent != "route_roles" or "Knowledge_Architect" not in reason:
        raise AssertionError(f"expected Mary bot alias to route to Knowledge_Architect, got {intent!r} / {reason!r}")

    routed_roles = requested_route_roles(
        root,
        "Send these notes over to both engineer and researcher for the n8n training plan.",
    )
    if set(routed_roles) != {"Engineer", "Researcher"}:
        raise AssertionError(f"expected Engineer and Researcher routing, got {routed_roles!r}")

    append_operator_message(root, "Hi", source="telegram", human_id="TestHuman")
    processed = run_once(root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed message, got {processed}")
    outbox = (root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(outbox, "I am here", "telegram-style reply")
    activity = activity_path(root).read_text(encoding="utf-8")
    assert_contains(activity, "CLASSIFY: presence", "activity classify trace")
    assert_contains(activity, "REPLY: Presence ping", "activity reply trace")
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

    intake_root = make_root()
    append_operator_message(intake_root, intake_text, source="telegram", human_id="TestHuman")
    processed = run_once(intake_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed task-intake message, got {processed}")
    intake_tasks = (intake_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    intake_wakes = (intake_root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    assert_contains(intake_tasks, "TASK-INTAKE-", "task intake task creation")
    assert_contains(intake_tasks, "Prioritize operator backlog", "task intake triage")
    assert_contains(intake_tasks, "Build a simple KPI update system", "task intake source item")
    if "TASK-WEB-" in intake_tasks:
        raise AssertionError("task intake created a web task")
    assert_contains(intake_wakes, "Engineer: intake_task", "task intake wake request")
    intake_outbox = (intake_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(intake_outbox, "I did not run a web search", "task intake honest reply")

    day_root = make_root()
    append_operator_message(day_root, day_text, source="telegram", human_id="TestHuman")
    processed = run_once(day_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed day-checklist message, got {processed}")
    day_tasks = (day_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    day_reminders = json.loads((day_root / "Runner" / "_reminders.json").read_text(encoding="utf-8"))
    day_outbox = (day_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(day_tasks, "TASK-TODAY-", "today checklist task ids")
    assert_contains(day_tasks, "Owner Role: Chief_of_Staff", "today checklist owner")
    if "Owner Role: Researcher" in day_tasks:
        raise AssertionError("today checklist should stay with Chief_of_Staff, not Researcher")
    if len(day_reminders) != 2:
        raise AssertionError(f"expected two check-in reminders, got {day_reminders!r}")
    assert_contains(day_outbox, "I saved today's checklist", "today checklist reply")

    capture_root = make_root()
    append_operator_message(
        capture_root,
        "The other major task is the proposal and quote generator for enterprise clients with sales and onboarding plans.",
        source="telegram",
        human_id="TestHuman",
    )
    append_operator_message(capture_root, "Yes make sure this is in the list of tasks to do so I don't forget about it", source="telegram", human_id="TestHuman")
    processed = run_once(capture_root)
    if processed != 2:
        raise AssertionError(f"expected 2 processed messages for task capture flow, got {processed}")
    captured_tasks = (capture_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    assert_contains(captured_tasks, "TASK-CHIEFCHAT-CAPTURE", "single task capture id")
    assert_contains(captured_tasks, "proposal and quote generator", "single task captured previous message")
    captured_outbox = (capture_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(captured_outbox, "I added it to the task list", "single task capture confirmation")

    role_root = make_root()
    append_operator_message(role_root, "Yes add the strategist role please", source="telegram", human_id="TestHuman")
    processed = run_once(role_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed role-add message, got {processed}")
    registry = (role_root / "Runner" / "ROLE_LAUNCH_REGISTRY.md").read_text(encoding="utf-8")
    roles_file = (role_root / "ROLES.md").read_text(encoding="utf-8")
    role_tasks = (role_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    assert_contains(registry, "Role: Strategist", "role registry add")
    assert_contains(registry, "Automation Ready: NO", "new role not automation-ready")
    assert_contains(roles_file, "Name: Strategist", "roles design add")
    assert_contains(role_tasks, "TASK-ROLE-SETUP-STRATEGIST", "role setup task")

    work_root = make_root()
    append_operator_message(work_root, work_text, source="telegram", human_id="TestHuman")
    processed = run_once(work_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed work-request message, got {processed}")
    work_tasks = (work_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    work_outbox = (work_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(work_tasks, "TASK-CHIEFCHAT-CAPTURE", "freeform work task creation")
    assert_contains(work_tasks, "list of leads", "freeform work request body")
    assert_contains(work_outbox, "I captured this", "freeform work truthful reply")

    human_root = make_root()
    write(
        human_root / "HUMANS.md",
        "\n".join(
            [
                "# HUMANS",
                "",
                "### HUMAN",
                "ID: TestHuman",
                "Full Name: Test Human",
                "Role: Operator",
                "Preferred Contact Methods:",
                "- telegram: test",
                "",
                "### HUMAN",
                "ID: MaryHelper0001",
                "Full Name: Mary Helper",
                "Role: Obsidian support",
                "Preferred Contact Methods:",
                "- email: mary@example.com",
            ]
        ),
    )
    append_operator_message(human_root, "Ask Mary to help you with obsidian", source="telegram", human_id="TestHuman")
    processed = run_once(human_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed human-assist message, got {processed}")
    human_tasks = (human_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    human_outbox = (human_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(human_tasks, "TASK-HUMAN-ASSIST-MARY", "human assist task")
    assert_contains(human_tasks, "WAITING_ON_HUMAN", "human assist non-runner status")
    assert_contains(human_outbox, "I have not marked them contacted yet", "human assist truthful reply")

    bot_route_root = make_root()
    write(
        bot_route_root / "ROLES.md",
        "\n".join(
            [
                "## Role",
                "Name: Knowledge Architect",
                "Lease File: `_heartbeat/Knowledge_Architect.md`",
                "Direct Message File: `_messages/Knowledge_Architect.md`",
            ]
        ),
    )
    write(
        bot_route_root / "_heartbeat" / "Knowledge_Architect.md",
        "\n".join(["# Mary", "**Name**: Mary", "**Status**: ACTIVE"]),
    )
    append_operator_message(bot_route_root, "Can you check with Mary on my latest lead list", source="telegram", human_id="TestHuman")
    processed = run_once(bot_route_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed bot-alias routing message, got {processed}")
    bot_tasks = (bot_route_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    bot_wakes = (bot_route_root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    assert_contains(bot_tasks, "TASK-CHIEFCHAT-KNOWLEDGE-ARCHITECT", "bot alias routed task")
    assert_contains(bot_tasks, "Owner Role: Knowledge_Architect", "bot alias owner role")
    if "TASK-HUMAN-ASSIST-MARY" in bot_tasks:
        raise AssertionError("Mary bot alias should not create a human-assist task")
    assert_contains(bot_wakes, "Knowledge_Architect", "bot alias wake request")

    skill_root = make_root()
    write(
        skill_root / "ROLES.md",
        "\n".join(
            [
                "## Role",
                "Name: VideoEditor",
                "Lease File: `_heartbeat/VideoEditor.md`",
                "Direct Message File: `_messages/VideoEditor.md`",
            ]
        ),
    )
    write(
        skill_root / "_heartbeat" / "VideoEditor.md",
        "\n".join(
            [
                "# VideoEditor Lease",
                "- Role: VideoEditor",
                "- Status: ACTIVE",
                "- Claimed By: Bob Editman",
                "- Harness: opencode",
            ]
        ),
    )
    skill_message = "Bob is doing a great job with transcription. Make sure Bob records this down in his Skill folder as one of his skills."
    if not is_skill_note_request(skill_root, skill_message):
        raise AssertionError("expected Bob skill-note request detection")
    intent, reason = detect_operator_intent(skill_root, skill_message)
    if intent != "skill_note" or "VideoEditor" not in reason:
        raise AssertionError(f"expected Bob skill-note intent for VideoEditor, got {intent!r} / {reason!r}")
    append_operator_message(skill_root, skill_message, source="telegram", human_id="TestHuman")
    processed = run_once(skill_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed skill-note message, got {processed}")
    skill_file = role_skill_file(skill_root, "VideoEditor").read_text(encoding="utf-8")
    skill_wakes = (skill_root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    skill_outbox = (skill_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(skill_file, "SKILL-NOTE-VIDEOEDITOR", "canonical role skill note")
    assert_contains(skill_file, "Bob Editman", "skill alias source")
    assert_contains(skill_file, "transcription", "skill note body")
    assert_contains(skill_wakes, "VideoEditor: skill_note", "skill note wake request")
    assert_contains(skill_outbox, "MEMORY/agents/VideoEditor/SKILLS.md", "skill note canonical reply path")

    takeover_root = make_root()
    write(
        takeover_root / "Runner" / "scheduled_role_runner.py",
        "import json, sys\n"
        "role = sys.argv[sys.argv.index('--role') + 1] if '--role' in sys.argv else ''\n"
        "print(json.dumps({'role': role, 'decision': 'run', 'action': 'launch', 'status': 'LAUNCHED', 'summary': 'fake launch'}))\n",
    )
    write(
        takeover_root / "ROLES.md",
        "\n".join(
            [
                "## Role",
                "Name: VideoEditor",
                "Lease File: `_heartbeat/VideoEditor.md`",
                "Direct Message File: `_messages/VideoEditor.md`",
            ]
        ),
    )
    write(
        takeover_root / "_heartbeat" / "VideoEditor.md",
        "\n".join(
            [
                "# VideoEditor Lease",
                "- Role: VideoEditor",
                "- Claimed By: Bob Editman",
                "- Status: ACTIVE",
                "- Harness: opencode",
                "- Provider: opencode",
                "- Model: minimax-m2.5-free",
            ]
        ),
    )
    takeover_message = "Can you take over Bob and complete his transcription work?"
    if not is_role_takeover_request(takeover_root, takeover_message):
        raise AssertionError("expected Bob role-takeover request detection")
    intent, reason = detect_operator_intent(takeover_root, takeover_message)
    if intent != "role_takeover" or "VideoEditor" not in reason:
        raise AssertionError(f"expected role_takeover intent for VideoEditor, got {intent!r} / {reason!r}")
    append_operator_message(takeover_root, takeover_message, source="telegram", human_id="TestHuman")
    processed = run_once(takeover_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed role-takeover message, got {processed}")
    takeover_tasks = (takeover_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    takeover_wakes = (takeover_root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    takeover_outbox = (takeover_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(takeover_tasks, "TASK-ROLE-TAKEOVER-VIDEOEDITOR", "role takeover task")
    assert_contains(takeover_wakes, "VideoEditor: role_takeover", "role takeover wake request")
    assert_contains(takeover_outbox, "I started a local `VideoEditor` run", "role takeover auto launch reply")
    registry = (takeover_root / "Runner" / "ROLE_LAUNCH_REGISTRY.md").read_text(encoding="utf-8")
    assert_contains(registry, "Role: VideoEditor", "role takeover auto registry")
    assert_contains(registry, "{AUTO_OPENCODE_CYCLE}", "role takeover heartbeat provider")

    repair_root = make_root()
    write(
        repair_root / "Runner" / "scheduled_role_runner.py",
        "import json, sys\n"
        "role = sys.argv[sys.argv.index('--role') + 1] if '--role' in sys.argv else ''\n"
        "print(json.dumps({'role': role, 'decision': 'run', 'action': 'launch', 'status': 'LAUNCHED', 'summary': 'fake launch'}))\n",
    )
    write(
        repair_root / "_heartbeat" / "Researcher.md",
        "\n".join(
            [
                "# Researcher Lease",
                "- Role: Researcher",
                "- Claimed By: Research Bot",
                "- Status: STALE",
                "- Harness: opencode",
                "- Provider: opencode",
                "- Model: minimax-m2.5-free",
            ]
        ),
    )
    append_operator_message(repair_root, "Take over Researcher and continue the research work", source="telegram", human_id="TestHuman")
    processed = run_once(repair_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed registry-repair takeover message, got {processed}")
    repair_outbox = (repair_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    repair_registry = (repair_root / "Runner" / "ROLE_LAUNCH_REGISTRY.md").read_text(encoding="utf-8")
    assert_contains(repair_outbox, "I started a local `Researcher` run", "role takeover registry repair launch reply")
    assert_contains(repair_registry, "Auto-created because the operator asked Chief_of_Staff", "role takeover registry repair block")
    assert_contains(repair_registry, "{AUTO_OPENCODE_CYCLE}", "role takeover registry repair provider")

    status_root = make_root()
    append_operator_message(status_root, "Status update", source="telegram", human_id="TestHuman")
    processed = run_once(status_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed status message, got {processed}")
    status_outbox = (status_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(status_outbox, "Current file", "status reply")
    assert_contains(status_outbox, "backed status", "status reply")
    assert_contains(status_outbox, "Wake log:", "status wake log truthfulness")
    assert_contains(status_outbox, "Deterministic actions are enabled", "status action contract")
    assert_contains(status_outbox, "I will not claim anything is actively executing", "status truthfulness")

    action_root = make_root()
    today_stamp = service.iso_now()
    write(
        action_root / "LAYER_TASK_LIST.md",
        "\n".join(
            [
                "# Tasks",
                "",
                "## TASK",
                "ID: TASK-WEB-OLD1",
                "Title: Old web request",
                "Project: operator-requests",
                "Owner Role: Researcher",
                "Status: TODO",
                "Priority: HIGH",
                "Created At: 2026-04-27T09:00:00-04:00",
                "",
                "## TASK",
                "ID: TASK-WEB-TODAY",
                "Title: Today's web request",
                "Project: operator-requests",
                "Owner Role: Researcher",
                "Status: TODO",
                "Priority: HIGH",
                f"Created At: {today_stamp}",
                "",
                "## TASK",
                "ID: TASK-OTHER-1",
                "Title: Build the control plane",
                "Project: harness",
                "Owner Role: Engineer",
                "Status: TODO",
                "Priority: HIGH",
                "Created At: 2026-04-27T10:00:00-04:00",
            ]
        ),
    )
    if actionable_task_count(action_root) != 3:
        raise AssertionError("expected 3 actionable test tasks before mutation")
    if not is_task_action_request(action_root, "Remove those web requests"):
        raise AssertionError("expected stale web cleanup to classify as task action")
    intent, _reason = detect_operator_intent(action_root, "Remove those web requests")
    if intent != "task_action":
        raise AssertionError(f"expected task_action intent for stale web cleanup, got {intent!r}")
    append_operator_message(action_root, "Remove those web requests", source="telegram", human_id="TestHuman")
    processed = run_once(action_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed stale web cleanup message, got {processed}")
    action_tasks = (action_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    action_outbox = (action_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(action_tasks, "ID: TASK-WEB-OLD1\nTitle: Old web request", "old web task kept in history")
    assert_contains(action_tasks, "Status: CANCELLED", "old web task cancelled")
    assert_contains(action_tasks, "ID: TASK-WEB-TODAY", "today web task kept")
    if not re.search(r"ID: TASK-WEB-TODAY.*?Status: TODO", action_tasks, flags=re.DOTALL):
        raise AssertionError("today web task should stay TODO by default")
    assert_contains(action_outbox, "Actionable tasks: 3 -> 2", "verified stale web before/after count")
    assert_contains(action_outbox, "Changed IDs: TASK-WEB-OLD1", "stale web changed id")
    if actionable_task_count(action_root) != 2:
        raise AssertionError("expected 2 actionable tasks after stale web cleanup")

    append_operator_message(action_root, "Complete TASK-OTHER-1", source="telegram", human_id="TestHuman")
    processed = run_once(action_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed complete-task message, got {processed}")
    action_tasks = (action_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    if not re.search(r"ID: TASK-OTHER-1.*?Status: DONE", action_tasks, flags=re.DOTALL):
        raise AssertionError("expected exact task completion to set DONE")
    action_outbox = (action_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(action_outbox, "Done. I completed 1 task(s) in the files.", "complete task verified reply")

    append_operator_message(action_root, "Reopen TASK-OTHER-1", source="telegram", human_id="TestHuman")
    processed = run_once(action_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed reopen-task message, got {processed}")
    action_tasks = (action_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    if not re.search(r"ID: TASK-OTHER-1.*?Status: TODO", action_tasks, flags=re.DOTALL):
        raise AssertionError("expected exact task reopen to set TODO")

    append_operator_message(action_root, "Assign TASK-OTHER-1 to Researcher", source="telegram", human_id="TestHuman")
    processed = run_once(action_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed assign-task message, got {processed}")
    action_tasks = (action_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    action_wakes = (action_root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    if not re.search(r"ID: TASK-OTHER-1.*?Owner Role: Researcher", action_tasks, flags=re.DOTALL):
        raise AssertionError("expected assignment to update Owner Role")
    assert_contains(action_wakes, "Researcher: reassigned_task:TASK-OTHER-1", "assign task wake request")

    append_operator_message(action_root, "Add note to TASK-OTHER-1: user confirmed this is priority one", source="telegram", human_id="TestHuman")
    processed = run_once(action_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed note-task message, got {processed}")
    action_tasks = (action_root / "LAYER_TASK_LIST.md").read_text(encoding="utf-8")
    assert_contains(action_tasks, "user confirmed this is priority one", "task note mutation")

    append_operator_message(action_root, "Cancel TASK-NOPE", source="telegram", human_id="TestHuman")
    processed = run_once(action_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed zero-match task action, got {processed}")
    action_outbox = (action_root / "_messages" / "human_TestHuman.md").read_text(encoding="utf-8")
    assert_contains(action_outbox, "I did not change anything because no matching task IDs were found.", "zero-match task action truthfulness")

    cleanup_root = make_root()
    write(
        cleanup_root / "LAYER_TASK_LIST.md",
        "\n".join(
            [
                "# Tasks",
                "",
                "## TASK",
                "ID: TASK-WEB-CLEANUP",
                "Title: Cleanup target",
                "Project: operator-requests",
                "Owner Role: Researcher",
                "Status: TODO",
                "Created At: 2026-04-27T09:00:00-04:00",
            ]
        ),
    )
    cleanup = cancel_stale_web_tasks(cleanup_root)
    if cleanup["before"] != 1 or cleanup["after"] != 0 or cleanup["ids"] != ["TASK-WEB-CLEANUP"]:
        raise AssertionError(f"expected cleanup command summary, got {cleanup!r}")

    if not is_role_wake_request(bot_route_root, "Wake Mary"):
        raise AssertionError("expected Mary bot alias wake detection")
    append_operator_message(bot_route_root, "Wake Mary", source="telegram", human_id="TestHuman")
    processed = run_once(bot_route_root)
    if processed != 1:
        raise AssertionError(f"expected 1 processed role-wake message, got {processed}")
    bot_wakes = (bot_route_root / "Runner" / "_wake_requests.md").read_text(encoding="utf-8")
    assert_contains(bot_wakes, "Knowledge_Architect: operator_wake", "bot alias role wake")

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
