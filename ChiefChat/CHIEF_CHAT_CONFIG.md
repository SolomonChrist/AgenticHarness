# CHIEF CHAT CONFIG

Configuration for the fast Chief_of_Staff chat service.

## Chat Model

Chat Provider: openai-compatible
Chat Model: local-model-name
OpenAI Compatible Base URL: http://127.0.0.1:1234/v1
Ollama Base URL: http://127.0.0.1:11434
OpenCode Command Template: opencode run "{PROMPT}" --model "{MODEL}" --dir "{WORKDIR}"
Reply Timeout Seconds: 20
Max Messages Per Pass: 3
Reply Max Tokens: 450

## Context Budget

Chief Soul Max Chars: 1200
Chief Always Memory Max Chars: 900
Human Memory Max Chars: 1200
Human Recent Files: 2
Human Recent File Max Chars: 500
Recent Chat Max Chars: 1400
System Roles Max: 8

## Browser

Browser Enabled: YES
Browser Inactivity Timeout Seconds: 30
Browser Max Run Seconds: 120
Browser Search Results: 5
Browser Pages To Read: 3
Browser Headless: NO

## Service

Poll Seconds: 0.5
Status Reply On Model Failure: YES

## Interaction Layer

Chief Interaction Mode: bounded-action-loop
Action Loop Max Steps: 4
Activity Log Enabled: YES
Activity Log Max Entries: 200
Role Takeover Auto Launch: YES
Role Takeover Infer Registry From Heartbeat: YES
Role Takeover Launch Timeout Seconds: 20
