import enum

class OptionMeta(enum.EnumMeta):
    """The backing metaclass behind `Option`."""
    def __iter__(self):
        # Enumeration constants should be kept in uppercase in source,
        # but rendered in lowercase on Discord clients. Since discord.py
        # extracts enumeration names via __iter__, we override it here.
        for name in self._member_names_:
            element = self._member_map_[name]
            element._name_ = element._name_.lower()
            yield element

class Option(enum.Enum, metaclass=OptionMeta):
    """A subclass of `enum.Enum` that renders enumeration names in lowercase."""
    pass

def possibilities(c: OptionMeta) -> str:
    """Transform an `Option` into a human-readable string of possibilities."""
    return f"{', '.join((e.name for e in list(c)))}"
