def estimate_tokens(payload):
    # If it's a list, assume it's just the messages (backwards compatibility)
    if isinstance(payload, list):
        messages = payload
    else:
        # Assume it's a dict with "messages"
        messages = payload.get("messages", [])

    # mega uproszczenie (na start OK)
    total = 0
    for m in messages:
        total += len(m.get("content", "").split())
    return int(total * 1.3)
