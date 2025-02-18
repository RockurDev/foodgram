def get_avatar_path(instance, filename: str) -> str:
    """Return the file path for user avatars."""
    return f'avatars/{instance.id}'
