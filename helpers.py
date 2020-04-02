def file2ext(filepath: str):
    """Convert a filepath into a Python import path."""
    filepath = filepath.replace("\\", ".").replace("/", ".").replace(".py", "")
    return filepath
