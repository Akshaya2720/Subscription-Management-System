from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from app.core.exceptions import InvalidStateTransitionException, BusinessRuleValidationException

VALID_TRANSITIONS = {
    "DRAFT": ["CONFIRMED", "ACTIVE", "CANCELLED"],
    "CONFIRMED": ["ACTIVE", "CANCELLED"],
    "ACTIVE": ["PAUSED", "CLOSED", "CANCELLED", "ACTIVE"],  # ACTIVE -> ACTIVE for renewal
    "PAUSED": ["ACTIVE", "CLOSED", "CANCELLED"],
    "CLOSED": [],
    "CANCELLED": [],
}


class SubscriptionLifecycleManager:
    @staticmethod
    def validate_transition(current_status: str, target_status: str, expiry_date: date = None) -> None:
        """Enforce strict subscription state machine transitions."""
        current = current_status.upper()
        target = target_status.upper()

        if current == target and target != "ACTIVE":
            raise InvalidStateTransitionException(
                current_status=current,
                target_status=target,
                reason=f"Subscription is already in '{current}' status.",
            )

        allowed = VALID_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise InvalidStateTransitionException(
                current_status=current,
                target_status=target,
                reason=f"Transition from '{current}' to '{target}' is not permitted.",
            )

        if target == "ACTIVE" and expiry_date and expiry_date < date.today():
            raise InvalidStateTransitionException(
                current_status=current,
                target_status=target,
                reason=f"Cannot activate an expired subscription (expired on {expiry_date}).",
            )

    @staticmethod
    def calculate_next_billing_date(start: date, frequency: str) -> date:
        """Calculate the next billing date based on the start date and frequency."""
        freq = frequency.upper()
        if freq == "DAILY":
            return start + timedelta(days=1)
        elif freq == "WEEKLY":
            return start + timedelta(weeks=1)
        elif freq == "MONTHLY":
            return start + relativedelta(months=1)
        elif freq == "YEARLY":
            return start + relativedelta(years=1)
        else:
            raise BusinessRuleValidationException(f"Unsupported billing frequency: {frequency}")

    @staticmethod
    def calculate_renewal_dates(current_expiry: date, current_next_billing: date, frequency: str, periods: int = 1) -> tuple:
        """Calculate advanced dates for renewal."""
        freq = frequency.upper()
        delta = None
        if freq == "DAILY":
            delta = timedelta(days=periods)
        elif freq == "WEEKLY":
            delta = timedelta(weeks=periods)
        elif freq == "MONTHLY":
            delta = relativedelta(months=periods)
        elif freq == "YEARLY":
            delta = relativedelta(years=periods)
        else:
            raise BusinessRuleValidationException(f"Unsupported billing frequency: {frequency}")

        new_expiry = (current_expiry + delta) if current_expiry else None
        new_next_billing = current_next_billing + delta
        return new_next_billing, new_expiry
