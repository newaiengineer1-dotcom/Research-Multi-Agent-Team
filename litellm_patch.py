# litellm_patch.py
"""
Monkey-patch LiteLLM to fix Groq compatibility issues:
  1. Strips 'cache_breakpoint' from messages (unsupported by Groq)
  2. Strips 'is_litellm' from top-level kwargs (unsupported by Groq)
  3. Removes tool_choice="none" (GPT-OSS models ignore it and call tools anyway,
     causing Groq to reject the request with tool_use_failed)
"""
import litellm
import re
import time

UNSUPPORTED_TOP_LEVEL_KEYS = ["is_litellm", "cache_breakpoint"]

_original_completion = litellm.completion
_original_acompletion = getattr(litellm, "acompletion", None)


def _clean_kwargs(kwargs: dict) -> dict:
    # 1. Strip unsupported top-level keys
    for key in UNSUPPORTED_TOP_LEVEL_KEYS:
        kwargs.pop(key, None)

    # 2. Strip cache_breakpoint from each message
    messages = kwargs.get("messages", [])
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict) and "cache_breakpoint" in msg:
                del msg["cache_breakpoint"]

    # 3. FIX: Remove tool_choice="none" — GPT-OSS models on Groq ignore it
    #    and call tools anyway, causing tool_use_failed. Setting it to "auto"
    #    lets the model call tools legitimately without Groq rejecting it.
    if kwargs.get("tool_choice") == "none":
        kwargs["tool_choice"] = "auto"

    return kwargs


def _patched_completion(*args, **kwargs):
    kwargs = _clean_kwargs(kwargs)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            return _original_completion(*args, **kwargs)
        except Exception as e:
            err = str(e)
            if "tool_use_failed" in err and attempt < max_retries - 1:
                # Model called a tool with malformed args. Retry with tools
                # removed entirely so the model produces a text answer.
                print("[PATCH] tool_use_failed — retrying without tools")
                kwargs.pop("tools", None)
                kwargs.pop("tool_choice", None)
                time.sleep(1)
                continue
            raise


async def _patched_acompletion(*args, **kwargs):
    kwargs = _clean_kwargs(kwargs)
    return await _original_acompletion(*args, **kwargs)


def apply_patch():
    litellm.completion = _patched_completion
    if _original_acompletion is not None:
        litellm.acompletion = _patched_acompletion
