# litellm_patch.py
"""
Monkey-patch LiteLLM to strip the 'cache_breakpoint' parameter that Groq's API
does not support. This resolves the error:
  litellm.BadRequestError: GroqException - 'messages.0' : for 'role:system' the
  following must be satisfied[('messages.0' : property 'cache_breakpoint' is
  unsupported)]

Inspired by the CrewAI community workaround for the identical 'is_litellm' bug.
"""
import litellm

# Save the original completion function before patching
_original_completion = litellm.completion


def _patched_completion(*args, **kwargs):
    """Strip unsupported keys from the request before sending to the provider."""
    # 1. Strip top-level cache_breakpoint if present
    kwargs.pop("cache_breakpoint", None)

    # 2. Strip cache_breakpoint from each message in the messages array
    messages = kwargs.get("messages", [])
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict) and "cache_breakpoint" in msg:
                del msg["cache_breakpoint"]

    # 3. Call the original completion with cleaned kwargs
    return _original_completion(*args, **kwargs)


def apply_patch():
    """
    Applies the monkey-patch. Call this once at application startup,
    before any CrewAI or LiteLLM calls are made.
    """
    litellm.completion = _patched_completion
    # Also patch the async variant if your code uses it
    if hasattr(litellm, "acompletion"):
        _original_acompletion = litellm.acompletion

        async def _patched_acompletion(*args, **kwargs):
            kwargs.pop("cache_breakpoint", None)
            messages = kwargs.get("messages", [])
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict) and "cache_breakpoint" in msg:
                        del msg["cache_breakpoint"]
            return await _original_acompletion(*args, **kwargs)

        litellm.acompletion = _patched_acompletion
