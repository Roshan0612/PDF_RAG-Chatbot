def build_retrieval_query(
    message: str,
    previous_messages: list
) -> str:
    previous_user_messages = [
        item.content
        for item in previous_messages
        if item.role == "user"
    ]

    if not previous_user_messages:
        return message

    recent_questions = previous_user_messages[-2:]

    conversation = "\n".join(
        recent_questions
    )

    return (
        f"Previous questions:\n"
        f"{conversation}\n\n"
        f"Current question:\n"
        f"{message}"
    )


def build_chat_history(
    messages: list
) -> str:
    history = []

    for message in messages:
        label = (
            "User"
            if message.role == "user"
            else "Assistant"
        )

        history.append(
            f"{label}: {message.content}"
        )

    return "\n".join(history)