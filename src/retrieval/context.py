from typing import List, Dict, Any


def get_context(
    messages: List[Dict[str, Any]],
    message_id: str,
    window: int = 2,
) -> List[Dict[str, Any]]:
    """
    Return nearby messages from the same conversation thread.

    This prevents unrelated global-chat messages from appearing
    in the context around a retrieved result.
    """

    target = None

    for message in messages:
        if message["id"] == message_id:
            target = message
            break

    if target is None:
        return []

    target_thread = target.get("thread_id")

    # Prefer messages from the same conversation thread.
    if target_thread:
        related_messages = [
            message
            for message in messages
            if message.get("thread_id") == target_thread
        ]
    else:
        related_messages = messages

    # Keep chronological order.
    related_messages = sorted(
        related_messages,
        key=lambda x: x["timestamp"],
    )

    target_index = None

    for index, message in enumerate(related_messages):
        if message["id"] == message_id:
            target_index = index
            break

    if target_index is None:
        return [target]

    start = max(0, target_index - window)
    end = min(
        len(related_messages),
        target_index + window + 1,
    )

    return related_messages[start:end]