# litellm_patch.py
"""
Monkey-patch LiteLLM to strip parameters that Groq's API rejects.

Fixes two distinct CrewAI -> Groq compatibility issues:
  1. 'cache_breakpoint' injected into system messages by CrewAI's cache layer
     Error: "'messages.0' : for 'role:system' ... property 'cache_breakpoint'
             is unsupported"
  2. 'is_litellm' injected at the top level by CrewAI's LLM wrapper
     Error: "is_litellm is unsupported"

Both keys are stripped from every outgoing completion request before it reaches
the provider. This is the documented CrewAI community workaround.
"""
import litellm

# Keys to strip from the top-level kwargs
UNSUPPORTED_TOP_LEVEL_KEYS = ["is_litellm", "cache_breakpoint"]

# Save the original functions before patching
_original_completion = litellm.completion
_original_acompletion = getattr(litellm, "acompletion", None)


def _clean_kwargs(kwargs: dict) -> dict:
    """Removes unsupported keys from top-level kwargs and from messages."""
    # 1. Strip unsupported top-level keys
    for key in UNSUPPORTED_TOP_LEVEL_KEYS:
        kwargs.pop(key, None)

    # 2. Strip cache_breakpoint from each message dict
    messages = kwargs.get("messages", [])
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict) and "cache_breakpoint" in msg:
                del msg["cache_breakpoint"]

    return kwargs


def _patched_completion(*args, **kwargs):
    """Sync completion wrapper."""
    kwargs = _clean_kwargs(kwargs)
    return _original_completion(*args, **kwargs)


async def _patched_acompletion(*args, **kwargs):
    """Async completion wrapper."""
    kwargs = _clean_kwargs(kwargs)
    return await _original_acompletion(*args, **kwargs)


def apply_patch():
    """
    Applies the monkey-patch. Call this ONCE at application startup,
    before any CrewAI or LiteLLM calls are made.
    """
    litellm.completion = _patched_completion
    if _original_acompletion is not None:
        litellm.acompletion = _patched_acompletion
