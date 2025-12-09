"""
Profile storage abstraction layer.
"""

from typing import Dict, Optional
from ..models.user_profile import UserProfile


class ProfileStorage:
    """
    In-memory profile storage.

    In production, this would be replaced with a database-backed implementation.
    """

    _profiles: Dict[str, UserProfile] = {}

    @classmethod
    def get(cls, profile_id: str) -> Optional[UserProfile]:
        """
        Get a profile by ID.

        Args:
            profile_id: Profile identifier

        Returns:
            UserProfile if found, None otherwise
        """
        return cls._profiles.get(profile_id)

    @classmethod
    def set(cls, profile_id: str, profile: UserProfile) -> None:
        """
        Store a profile.

        Args:
            profile_id: Profile identifier
            profile: UserProfile instance
        """
        cls._profiles[profile_id] = profile

    @classmethod
    def delete(cls, profile_id: str) -> bool:
        """
        Delete a profile.

        Args:
            profile_id: Profile identifier

        Returns:
            True if deleted, False if not found
        """
        if profile_id in cls._profiles:
            del cls._profiles[profile_id]
            return True
        return False

    @classmethod
    def exists(cls, profile_id: str) -> bool:
        """
        Check if a profile exists.

        Args:
            profile_id: Profile identifier

        Returns:
            True if exists, False otherwise
        """
        return profile_id in cls._profiles

    @classmethod
    def clear(cls) -> None:
        """Clear all profiles (mainly for testing)."""
        cls._profiles.clear()

    @classmethod
    def get_all(cls) -> Dict[str, UserProfile]:
        """
        Get all stored profiles.

        Returns:
            Dictionary of profile_id -> UserProfile
        """
        return cls._profiles.copy()

    @classmethod
    def get_first(cls) -> Optional[UserProfile]:
        """
        Get the first available profile (useful for single-user scenarios).

        Returns:
            First UserProfile if available, None otherwise
        """
        if cls._profiles:
            return list(cls._profiles.values())[0]
        return None
