import os
import re

# Separate controls for input tokens (compressing messages) and output tokens (prompt injection)
CAVEMAN_INPUT_ENABLED = os.getenv("CAVEMAN_INPUT_ENABLED", "false").lower() == "true"
CAVEMAN_OUTPUT_ENABLED = os.getenv("CAVEMAN_OUTPUT_ENABLED", "false").lower() == "true"
CAVEMAN_LEVEL = os.getenv("CAVEMAN_LEVEL", "full")

CAVEMAN_OUTPUT_PROMPT = """Respond terse like smart caveman. All technical substance stay. Only fluff die.
ACTIVE EVERY RESPONSE. No revert after many turns. No filler drift. Still active if unsure. Off only: "stop caveman" / "normal mode".
Current Level: {level}.
Rules: Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms (big not extensive, fix not "implement a solution for"). Technical terms exact. Code blocks unchanged. Errors quoted exact.
Pattern: `[thing] [action] [reason]. [next step].`
"""

def compress_text(text: str) -> str:
    """Very basic token-saving text compressor (caveman style)"""
    if not text:
        return text
    
    # Do not compress code blocks
    parts = re.split(r'(```[\s\S]*?```)', text)
    compressed_parts = []
    
    # Basic word list to drop for 'caveman' input
    drop_words = {
        'a', 'an', 'the', 'just', 'really', 'basically', 'actually', 'simply',
        'please', 'thank', 'you', 'could', 'would', 'should', 'be', 'very'
    }
    
    for part in parts:
        if part.startswith('```'):
            compressed_parts.append(part)
        else:
            # Drop common filler words and extra spaces
            words = re.findall(r'\b\w+\b|[^\w\s]', part)
            filtered_words = [w for w in words if w.lower() not in drop_words]
            compressed_parts.append(" ".join(filtered_words))
            
    return " ".join(compressed_parts)

def apply_caveman(messages: list) -> list:
    # 1. Input compression (if enabled)
    if CAVEMAN_INPUT_ENABLED:
        for msg in messages:
            if msg.get("role") in ["user", "assistant"] and "content" in msg:
                msg["content"] = compress_text(msg["content"])
                
    # 2. Output prompt injection (if enabled)
    if not CAVEMAN_OUTPUT_ENABLED:
        return messages

    prompt = CAVEMAN_OUTPUT_PROMPT.format(level=CAVEMAN_LEVEL)
    
    # Check if there's already a system message
    system_msg_index = -1
    for i, msg in enumerate(messages):
        if msg.get("role") == "system":
            system_msg_index = i
            break
            
    if system_msg_index != -1:
        # Append to existing system message
        messages[system_msg_index]["content"] += "\n\n" + prompt
    else:
        # Insert new system message at the beginning
        messages.insert(0, {"role": "system", "content": prompt})
        
    return messages
