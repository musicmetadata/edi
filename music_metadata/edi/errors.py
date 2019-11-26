class FileError(ValueError):
    """Makes the file invalid."""
    pass

# class SequenceError(ValueError):
#     """File is invalid, but so"""
#     pass
# #
# class FieldError(ValueError):
#     pass

class FieldWarning(ValueError):
    pass

class FieldError(ValueError):
    pass

class RecordError(ValueError):
    pass