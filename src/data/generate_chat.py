import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from src.data.models import ChatMessage
from src.data.templates import (
    PARTICIPANTS,
    CASUAL_MESSAGES,
    HINGLISH_MESSAGES,
    FORWARDED_MESSAGES,
    MEDIA_MESSAGES,
    EMOJIS,
)
from src.data.decision_threads import DECISION_THREADS


SEED = 20260912

START_DATE = datetime(2026, 3, 1, 8, 0, 0)
END_DATE = datetime(2026, 8, 31, 23, 59, 59)

TARGET_MESSAGES = 5000


random.seed(SEED)


def random_timestamp(start, end):
    seconds = int((end - start).total_seconds())

    offset = random.randint(0, seconds)

    return start + timedelta(seconds=offset)


def introduce_typo(text):
    if len(text) < 5:
        return text

    if random.random() > 0.12:
        return text

    words = text.split()

    if not words:
        return text

    index = random.randrange(len(words))
    word = words[index]

    if len(word) > 3:
        position = random.randrange(len(word))
        word = word[:position] + word[position + 1:]

        words[index] = word

    return " ".join(words)


def generate_random_message():
    roll = random.random()

    if roll < 0.42:
        text = random.choice(CASUAL_MESSAGES)
        message_type = "text"
        forwarded = False
        media_type = None

    elif roll < 0.78:
        text = random.choice(HINGLISH_MESSAGES)
        message_type = "text"
        forwarded = False
        media_type = None

    elif roll < 0.87:
        text = random.choice(FORWARDED_MESSAGES)
        message_type = "forwarded"
        forwarded = True
        media_type = None

    elif roll < 0.95:
        media_type, text = random.choice(MEDIA_MESSAGES)
        message_type = "media"
        forwarded = False

    else:
        text = random.choice(EMOJIS)
        message_type = "text"
        forwarded = False
        media_type = None

    return {
        "text": introduce_typo(text),
        "message_type": message_type,
        "forwarded": forwarded,
        "media_type": media_type,
    }


def create_decision_messages(start_id, thread_id, start_time):

    messages = []

    current_time = start_time
    current_id = start_id

    ground_truth = []

    for sender, text in DECISION_THREADS[thread_id]["messages"]:

        message_id = f"msg_{current_id:04d}"

        message = ChatMessage(
            id=message_id,
            timestamp=current_time.isoformat(),
            sender=sender,
            text=text,
            message_type="text",
            thread_id=thread_id,
        )

        messages.append(message)

        if (
            "locked" in text.lower()
            or "let's do" in text.lower()
            or "theek hai" in text.lower()
        ):
            ground_truth.append({
                "message_id": message_id,
                "thread_id": thread_id,
                "topic": DECISION_THREADS[thread_id]["topic"],
                "text": text,
            })

        current_id += 1

        current_time += timedelta(
            minutes=random.randint(2, 25)
        )

    return messages, current_id, ground_truth


def generate_chat():

    messages = []

    ground_truth = []

    next_id = 1

    # --------------------------------------------------
    # Insert the three important decision conversations
    # --------------------------------------------------

    decision_configs = [
        ("trip_manali", datetime(2026, 7, 18, 18, 0)),
        ("event_venue", datetime(2026, 6, 12, 17, 30)),
        ("project_stack", datetime(2026, 8, 7, 19, 0)),
    ]

    for thread_id, start_time in decision_configs:

        thread_messages, next_id, thread_truth = (
            create_decision_messages(
                next_id,
                thread_id,
                start_time,
            )
        )

        messages.extend(thread_messages)
        ground_truth.extend(thread_truth)

    # --------------------------------------------------
    # Generate background conversation
    # --------------------------------------------------

    while len(messages) < TARGET_MESSAGES:

        timestamp = random_timestamp(
            START_DATE,
            END_DATE,
        )

        sender = random.choice(PARTICIPANTS)

        generated = generate_random_message()

        message = ChatMessage(
            id=f"msg_{next_id:04d}",
            timestamp=timestamp.isoformat(),
            sender=sender,
            text=generated["text"],
            message_type=generated["message_type"],
            forwarded=generated["forwarded"],
            media_type=generated["media_type"],
        )

        messages.append(message)

        next_id += 1

    # --------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------

    messages.sort(
        key=lambda message: message.timestamp
    )

    # --------------------------------------------------
    # Save chat
    # --------------------------------------------------

    output_dir = Path("data/raw")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    chat_path = output_dir / "chat.json"

    with open(
        chat_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            [message.to_dict() for message in messages],
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------
    # Save ground truth
    # --------------------------------------------------

    truth_path = output_dir / "ground_truth.json"

    with open(
        truth_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            ground_truth,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("=" * 60)
    print("CHATRECALL DATASET GENERATED")
    print("=" * 60)

    print(f"Messages: {len(messages)}")
    print(f"Participants: {len(PARTICIPANTS)}")
    print(f"Seed: {SEED}")

    print()
    print("Decision threads:")

    for thread_id in DECISION_THREADS:
        print(f"  - {thread_id}")

    print()
    print(f"Chat: {chat_path}")
    print(f"Ground truth: {truth_path}")


if __name__ == "__main__":
    generate_chat()