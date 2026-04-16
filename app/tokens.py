def estimate_tokens(messages):
    # mega uproszczenie (na start OK)
    total = 0
    for m in messages:
        total += len(m.get("content", "").split())
    return int(total * 1.3)
