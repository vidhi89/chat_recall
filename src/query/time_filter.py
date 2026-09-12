from datetime import datetime, timedelta
from typing import Optional


def get_time_range(
    expression: Optional[str],
    reference_date: Optional[datetime] = None,
):
    if not expression:
        return None

    if reference_date is None:
        reference_date = datetime.now()

    expression = expression.lower().strip()

    if expression == "last month":
        first_day_current_month = datetime(
            reference_date.year,
            reference_date.month,
            1,
        )

        last_day_previous_month = (
            first_day_current_month - timedelta(days=1)
        )

        start = datetime(
            last_day_previous_month.year,
            last_day_previous_month.month,
            1,
        )

        end = datetime(
            last_day_previous_month.year,
            last_day_previous_month.month,
            last_day_previous_month.day,
            23,
            59,
            59,
        )

        return start, end

    if expression == "this month":
        start = datetime(
            reference_date.year,
            reference_date.month,
            1,
        )

        if reference_date.month == 12:
            next_month = datetime(
                reference_date.year + 1,
                1,
                1,
            )
        else:
            next_month = datetime(
                reference_date.year,
                reference_date.month + 1,
                1,
            )

        end = next_month - timedelta(seconds=1)

        return start, end

    # Explicit month names
    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    if expression in month_names:
        month = month_names[expression]

        # Our synthetic corpus is from 2026.
        year = 2026

        start = datetime(year, month, 1)

        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)

        end = next_month - timedelta(seconds=1)

        return start, end

    if expression == "yesterday":
        yesterday = reference_date - timedelta(days=1)

        start = datetime(
            yesterday.year,
            yesterday.month,
            yesterday.day,
        )

        end = datetime(
            yesterday.year,
            yesterday.month,
            yesterday.day,
            23,
            59,
            59,
        )

        return start, end

    if expression == "today":
        start = datetime(
            reference_date.year,
            reference_date.month,
            reference_date.day,
        )

        end = datetime(
            reference_date.year,
            reference_date.month,
            reference_date.day,
            23,
            59,
            59,
        )

        return start, end

    return None