"""
Music Metadata - EDI is a base library for several EDI-based formats by CISAC,
most notably Common Works Registration (CWR) and Common Royalty Distribution (CRD).

This file contains error definitions."""


class FileError(ValueError):
    """Makes the file invalid."""
    pass


class FieldWarning(ValueError):
    """Makes the field invalid, but not the record."""
    pass


class FieldError(ValueError):
    """Makes the field invalid, and the record."""
    pass


class RecordError(ValueError):
    """Makes the record invalid."""
    pass
