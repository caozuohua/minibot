"""Lark message card templates."""


def task_start_card(goal: str, plan: str = "") -> dict:
    """Task start card showing the goal and plan."""
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"\U0001f3af **Task Started**\n\n**Goal:** {goal}",
            },
        }
    ]

    if plan:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"\n\U0001f4cb **Plan:**\n{plan}",
                },
            }
        )

    return {
        "header": {
            "title": {"tag": "plain_text", "content": "MiniBot — Task Started"},
            "template": "blue",
        },
        "elements": elements,
    }


def task_progress_card(step: int, total: int, detail: str) -> dict:
    """Progress update card."""
    percentage = int((step / total) * 100) if total > 0 else 0

    return {
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"MiniBot — Progress ({step}/{total})",
            },
            "template": "cyan",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (f"**Step {step}/{total}** ({percentage}%)\n\n{detail}"),
                },
            },
            {
                "tag": "progress",
                "percentage": percentage,
                "color": "blue",
            },
        ],
    }


def task_result_card(
    summary: str,
    details: str = "",
    mode: str = "react",
    iterations: int = 0,
    elapsed: float = 0,
) -> dict:
    """Task completion result card."""
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"\u2705 **Task Completed**\n\n{summary}",
            },
        },
    ]

    if details:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"\n\U0001f4dd **Details:**\n{details}",
                },
            }
        )

    elements.append(
        {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": (
                        f"Mode: {mode} | Iterations: {iterations} | "
                        f"Time: {elapsed:.1f}s"
                    ),
                },
            ],
        }
    )

    return {
        "header": {
            "title": {"tag": "plain_text", "content": "MiniBot — Result"},
            "template": "green",
        },
        "elements": elements,
    }


def task_error_card(error: str, partial_result: str = "") -> dict:
    """Error notification card."""
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"\u274c Error\n\n{error}",
            },
        },
    ]

    if partial_result:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"\n\U0001f4cb Partial Result:\n{partial_result}",
                },
            }
        )

    return {
        "header": {
            "title": {"tag": "plain_text", "content": "MiniBot — Error"},
            "template": "red",
        },
        "elements": elements,
    }
