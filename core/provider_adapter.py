import os
import json
import math
import time
import urllib.request
import urllib.error
from openai import OpenAI

class ProviderAdapter:
    def __init__(self, provider_profile_path):
        self.profile_path = provider_profile_path
        self.load_profile()
        
    def load_profile(self):
        with open(self.profile_path, 'r', encoding='utf-8-sig') as f:
            self.profile = json.load(f)
        
        self.provider = self.profile.get("provider", "PLACEHOLDER").lower()
        self.model = self.profile.get("model", "PLACEHOLDER")
        self.api_base = self.profile.get("api_base", "")
        self.enabled = self.profile.get("enabled", False)
        
        # Legacy migration fallback
        self.api_key = self.profile.get("api_key", "")
        if not self.api_key and "api_key_env" in self.profile:
            env_val = self.profile.get("api_key_env", "")
            if env_val.startswith("sk-") or len(env_val) > 40:
                self.api_key = env_val
            else:
                self.api_key = os.environ.get(env_val, "")
        
        if not self.enabled:
            self.client = None
            return

        api_key = self.api_key if self.api_key else "not-set"

        def normalize_base_url(url, provider=None):
            if not url:
                return url
            normalized = url.rstrip("/")
            if provider == "lmstudio" and not normalized.endswith("/v1"):
                normalized += "/v1"
            if provider == "ollama" and not normalized.endswith("/v1"):
                normalized += "/v1"
            return normalized + "/"
        
        if self.provider == "openai":
            if self.api_base:
                self.client = OpenAI(api_key=api_key, base_url=normalize_base_url(self.api_base, self.provider), timeout=30.0)
            else:
                self.client = OpenAI(api_key=api_key, timeout=30.0)
        elif self.provider == "anthropic":
            self.client = "ANTHROPIC_NATIVE"
        elif self.provider in ("lmstudio", "ollama", "openrouter"):
            # Generic OpenAI-compatible injection for most providers
            api_base = self.api_base
            if self.provider == "lmstudio" and not api_base: api_base = "http://localhost:1234/v1"
            if self.provider == "ollama" and not api_base: api_base = "http://localhost:11434/v1"
            api_base = normalize_base_url(api_base, self.provider)
            
            headers = {}
            if self.provider == "openrouter":
                headers["X-Title"] = "AgenticHarness"
                headers["HTTP-Referer"] = "https://github.com/agentic-harness"
            
            self.client = OpenAI(base_url=api_base, api_key=api_key, timeout=30.0, default_headers=headers)
        elif self.provider == "mock":
            self.client = "MOCK"
        else:
            self.client = None

    def test_reasoning(self):
        """Perform a 1-token completion to verify the provider is actually functional."""
        if not self.enabled: return False, "Provider disabled"
        if self.provider == "mock": return True, "MOCK MODE ACTIVE"
        if not self.client: return False, f"Provider '{self.provider}' not supported"
        if self.model == "PLACEHOLDER": return False, "Model not configured"
        
        try:
            if self.provider == "anthropic":
                return self._test_anthropic_native()
            
            # OpenAI-compatible Reasoning Test
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                timeout=15.0
            )
            if response.choices:
                return True, "Ready"
            return False, "Empty response"
        except Exception as e:
            err = str(e).lower()
            if "401" in err or "auth" in err or "key" in err or "403" in err: 
                return False, "Invalid credentials"
            if "404" in err or "model" in err: 
                return False, f"Model unavailable ({self.model})"
            if "connect" in err or "refused" in err: 
                return False, "Endpoint unreachable"
            return False, f"Reasoning failure: {str(e)}"

    def _test_anthropic_native(self):
        """Native urllib implementation for Anthropic /v1/messages"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": "AgenticHarness-V1-Verification"
        }
        data = {
            "model": self.model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    return True, "Ready"
                return False, f"Anthropic error: {response.status}"
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code in (401, 403): return False, "Invalid credentials"
            if e.code == 404: return False, f"Model unavailable ({self.model})"
            return False, f"Anthropic HTTP {e.code}: {body[:100]}"
        except Exception as e:
            return False, f"Anthropic failure: {str(e)}"

    def get_response(self, system_prompt, user_prompt):
        if not self.enabled:
            return "[ERROR] Provider is disabled in ProviderProfile.json."
            
        if self.provider == "mock":
            return f"[MOCK_ORCHESTRATION] Mock response for: {user_prompt[:50]}..."

        if not self.client:
            return f"[ERROR] Provider '{self.provider}' not configured or supported."
        
        if self.model == "PLACEHOLDER":
            return "[ERROR] Model not configured in ProviderProfile.json."

        try:
            if self.provider == "anthropic":
                return self._get_anthropic_response_native(system_prompt, user_prompt)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[ERROR] Provider failure: {str(e)}"

    def _get_anthropic_response_native(self, system_prompt, user_prompt):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                return resp_data["content"][0]["text"]
        except Exception as e:
            return f"[ERROR] Anthropic native failure: {str(e)}"

if __name__ == "__main__":
    print("ProviderAdapter refinement complete.")
