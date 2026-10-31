from fastapi import HTTPException, status


class EntityNotFoundException(HTTPException):
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with ID '{entity_id}' not found.",
        )


class DuplicateEntityException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )


class InvalidStateTransitionException(HTTPException):
    def __init__(self, current_status: str, target_status: str, reason: str = ""):
        msg = f"Invalid state transition from '{current_status}' to '{target_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )


class BusinessRuleValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=422,
            detail=detail,
        )
