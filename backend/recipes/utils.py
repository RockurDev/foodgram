def get_recipe_media_path(instance, filename: str) -> str:
    """Generate a path for storing recipe media files."""
    return f'recipies/{instance.author.id}/{filename}'
