"""Authentication API routes.

Provides:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login with JWT cookie
- POST /api/v1/auth/logout - User logout
- POST /api/v1/auth/forgot-password - Request password reset token
- POST /api/v1/auth/reset-password - Reset password with token
"""

from typing import Any
from uuid import UUID

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.exceptions import InvalidResetPasswordToken, UserAlreadyExists
from pydantic import BaseModel, EmailStr, Field

from app.core.auth import (
    UserManager,
    auth_backend,
    current_active_user,
    fastapi_users,
    get_user_manager,
)
from app.core.redis import (
    RedisSessionStore,
    create_session_data,
    get_client_ip,
    get_redis_client,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_session_store() -> RedisSessionStore:
    """Get Redis session store instance."""
    client = await get_redis_client()
    return RedisSessionStore(client)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "REGISTER_USER_ALREADY_EXISTS"},
        422: {"description": "Validation error (e.g., password too short)"},
    },
)
async def register(
    request: Request,
    background_tasks: BackgroundTasks,
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
) -> Any:
    """Register a new user.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager for async audit logging.
        user_create: User registration data (email, password).
        user_manager: FastAPI-Users user manager.

    Returns:
        UserRead: The created user.

    Raises:
        HTTPException: 400 if email already exists.
    """
    try:
        user = await user_manager.create(user_create, safe=True, request=request)
    except UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="REGISTER_USER_ALREADY_EXISTS",
        ) from exc

    # Fire-and-forget audit logging
    ip_address = get_client_ip(request)
    background_tasks.add_task(_log_audit_event, "user.registered", user.id, ip_address)

    return user


@router.post(
    "/login",
    responses={
        200: {"description": "Successful login, JWT cookie set"},
        400: {"description": "LOGIN_BAD_CREDENTIALS"},
        429: {"description": "Too many failed attempts"},
    },
)
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
) -> Response:
    """Log in a user and set JWT cookie.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager.
        credentials: Login credentials (username=email, password).
        user_manager: FastAPI-Users user manager.

    Returns:
        Response: Response with Set-Cookie header for JWT.

    Raises:
        HTTPException: 400 for bad credentials, 429 for rate limiting.
    """
    session_store = await _get_session_store()
    ip_address = get_client_ip(request)

    # Check rate limiting before attempting login
    failed_attempts = await session_store.get_failed_attempts(ip_address)
    if session_store.is_rate_limited(failed_attempts):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    # Attempt authentication using FastAPI-Users
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        # Increment failed attempts
        await session_store.increment_failed_attempts(ip_address)
        background_tasks.add_task(
            _log_audit_event, "user.login_failed", None, ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LOGIN_BAD_CREDENTIALS",
        )

    # Successful login - reset failed attempts and store session
    await session_store.reset_failed_attempts(ip_address)
    session_data = create_session_data(ip_address)
    await session_store.store_session(user.id, session_data)

    # Generate JWT response with cookie
    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(user)
    response = await auth_backend.transport.get_login_response(token)

    # Audit logging
    background_tasks.add_task(_log_audit_event, "user.login", user.id, ip_address)

    return response


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully logged out"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(fastapi_users.current_user(active=True)),
) -> Response:
    """Log out the current user.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager.
        user: Current authenticated user.

    Returns:
        Response: Response with cleared JWT cookie.
    """
    session_store = await _get_session_store()
    ip_address = get_client_ip(request)

    # Invalidate session in Redis
    await session_store.invalidate_session(user.id)

    # Clear the JWT cookie
    response = await auth_backend.transport.get_logout_response()

    # Audit logging
    background_tasks.add_task(_log_audit_event, "user.logout", user.id, ip_address)

    return response


async def _log_audit_event(
    action: str,
    user_id: UUID | None,
    ip_address: str,
    details: dict | None = None,
) -> None:
    """Fire-and-forget audit logging.

    This function is called as a background task to not block the response.
    Actual database write is delegated to AuditService (Task 7).

    Args:
        action: The audit action name (e.g., "user.registered").
        user_id: The user's UUID (None for failed login attempts).
        ip_address: The client's IP address.
        details: Additional details to log.
    """
    try:
        # Import here to avoid circular imports
        from app.services.audit_service import audit_service

        await audit_service.log_event(
            action=action,
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            details=details,
            ip_address=ip_address,
        )
    except Exception:
        # Audit logging should never fail the request
        # In production, this would log to error monitoring
        pass


# ============================================================================
# Password Reset Schemas
# ============================================================================


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot-password endpoint."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for reset-password endpoint."""

    token: str
    password: str = Field(..., min_length=8)


# ============================================================================
# Password Reset Endpoints
# ============================================================================


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {
            "description": "Password reset requested (always returns 202 for security)"
        },
    },
)
async def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    body: ForgotPasswordRequest,
    user_manager: UserManager = Depends(get_user_manager),
) -> dict[str, str]:
    """Request a password reset token.

    Always returns 202 Accepted regardless of whether the email exists
    to prevent email enumeration attacks.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager for async audit logging.
        body: Request body containing email.
        user_manager: FastAPI-Users user manager.

    Returns:
        dict: Status message.
    """
    ip_address = get_client_ip(request)

    try:
        # Try to get user by email
        user = await user_manager.get_by_email(body.email)

        # Generate reset token using FastAPI-Users
        token = await user_manager.forgot_password(user, request)

        # Log token to console (mock email for MVP)
        logger.info(
            "password_reset_token_generated",
            user_email=user.email,
            user_id=str(user.id),
            token=token,
            reset_url=f"/reset-password?token={token}",
        )

        # Audit logging
        background_tasks.add_task(
            _log_audit_event,
            "user.password_reset_requested",
            user.id,
            ip_address,
        )
    except Exception:
        # User not found or other error - still return 202 for security
        # Log for debugging but don't expose to client
        logger.debug("forgot_password_user_not_found", email=body.email)

    return {"detail": "Password reset requested"}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password successfully reset"},
        400: {"description": "Invalid or expired reset token"},
        422: {"description": "Validation error (password requirements)"},
    },
)
async def reset_password(
    request: Request,
    background_tasks: BackgroundTasks,
    body: ResetPasswordRequest,
    user_manager: UserManager = Depends(get_user_manager),
) -> dict[str, str]:
    """Reset password using a valid token.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager for async audit logging.
        body: Request body containing token and new password.
        user_manager: FastAPI-Users user manager.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: 400 if token is invalid or expired.
    """
    ip_address = get_client_ip(request)

    try:
        # Reset password using FastAPI-Users
        user = await user_manager.reset_password(body.token, body.password, request)

        # Invalidate all existing sessions for this user
        session_store = await _get_session_store()
        sessions_invalidated = await session_store.invalidate_all_user_sessions(user.id)

        logger.info(
            "password_reset_completed",
            user_id=str(user.id),
            sessions_invalidated=sessions_invalidated,
        )

        # Audit logging
        background_tasks.add_task(
            _log_audit_event,
            "user.password_reset",
            user.id,
            ip_address,
            {"sessions_invalidated": sessions_invalidated},
        )

        return {"detail": "Password has been reset"}

    except InvalidResetPasswordToken as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RESET_PASSWORD_INVALID_TOKEN",
        ) from exc


# ============================================================================
# Session Refresh Endpoint
# ============================================================================


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Session refreshed, new JWT cookie set"},
        401: {"description": "Not authenticated or session expired"},
    },
)
async def refresh_session(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(current_active_user),
) -> Response:
    """Refresh the current session, extending its lifetime.

    This endpoint is called by the frontend to implement sliding sessions.
    When the user is active, the frontend periodically calls this endpoint
    to get a new JWT token with full session lifetime, preventing timeout
    while the user is actively using the application.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager.
        user: Current authenticated user (validates JWT is still valid).

    Returns:
        Response: Response with new Set-Cookie header for refreshed JWT.
    """
    session_store = await _get_session_store()
    ip_address = get_client_ip(request)

    # Update session data in Redis with refreshed timestamp
    session_data = create_session_data(ip_address)
    await session_store.store_session(user.id, session_data)

    # Generate new JWT with full session lifetime
    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(user)
    response = await auth_backend.transport.get_login_response(token)

    # Audit logging (optional - can be verbose, consider throttling in production)
    background_tasks.add_task(
        _log_audit_event, "user.session_refreshed", user.id, ip_address
    )

    return response
