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

## Browser

Browser Enabled: YES
Browser Inactivity Timeout Seconds: 30
Browser Max Run Seconds: 120
Browser Headless: NO

## Service

Poll Seconds: 0.5
Status Reply On Model Failure: YES
