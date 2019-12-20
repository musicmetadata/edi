"""
Music Metadata - EDI is a base library for several EDI-based formats by CISAC,
most notably Common Works Registration (CWR) and Common Royalty Distribution
(CRD).

This file contains record definitions."""

import collections

from .fields import *


class EdiRecordMeta(type):
    """Meta class for EdiRecord"""

    def __new__(mcs, name, bases, classdict):
        classdict['_fields'] = collections.OrderedDict()
        for base in bases:
            if hasattr(base, '_fields'):
                classdict['_fields'].update(base._fields)
        for label, field in classdict.items():
            if isinstance(field, EdiField):
                classdict['_fields'][label] = field
        return super().__new__(mcs, name, bases, classdict)


class EdiRecord(object, metaclass=EdiRecordMeta):
    """Base class for all records."""

    record_type = EdiField(size=3, mandatory=True)

    def __init__(self, line=None, sequence=None):
        super().__init__()
        self.sequence = sequence
        self.line = line
        self.rest = ''
        self.type = None
        self.valid = True
        self.errors = collections.OrderedDict()
        if self.line:
            if len(self.line) > 3:
                self.split_into_fields()
                self.type = line[0:3]
            else:
                raise FileError(f'Record too short: {line}')

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'record_type' and self.type is None:
            self.type = key

    def to_edi(self):
        output = ''
        for label, field in self._fields.items():
            value = getattr(self, label)
            s = field.to_edi(value)
            output += s
        else:
            output += self.rest
        return output

    def __str__(self):
        return self.to_edi()

    def warning(self, field, error):
        """Add an error, do not invalidate."""
        if field and field not in self.labels:
            labels = ', '.join(self.labels)
            raise AttributeError(f'No such field { field } in { labels }')
        self.errors[field] = error

    def error(self, field, error):
        """Add an error and invalidate."""
        self.valid = False
        self.warning(field, error)

    def split_into_fields(self):
        """Split a record into fields, extend with blanks if truncated."""
        pos = 0
        specified_length = 0
        actual_length = len(self.line)

        # Add blanks at the end if missing
        for field in self.get_fields().values():
            specified_length += field._size
        if specified_length > actual_length:
            self.line = self.line.ljust(specified_length)

        for label, field in self.get_fields().items():
            start = pos
            end = pos + field._size
            pos += field._size
            value = self.line[start:end]
            if start < actual_length < end:
                self.warning(label, FieldWarning('Field truncated'))
            elif end > actual_length:
                if field._mandatory:
                    self.error(label, RecordError('Mandatory field missing'))
                else:
                    self.warning(label, FieldWarning(
                        'Field missing at the end of the line.'))
            try:
                setattr(self, label, value)
            except FieldWarning as e:
                self.warning(label, e)
            except FieldError as e:
                self.error(label, e)
            except (RecordError, FileError) as e:
                self.error(label, e)
                raise
        else:
            self.rest = self.line[pos:]

    def get_fields(self):
        return self._fields

    @property
    def fields(self):
        return self.get_fields().values()

    @property
    def labels(self):
        return self.get_fields().keys()

    def to_html(self):
        classes = f'record { self.type.lower() }'
        if not self.valid:
            classes += ' invalid'
        output = f'<span class="{ classes }">'
        for field in self.fields:
            value = getattr(self, field._name)
            s = field.to_html(
                value, f'{ field._name }', self.errors.get(field._name))
            output += s
        else:
            output += EdiField.to_html(
                None, self.rest, label='', error=self.errors.get(None))
        output += '</span>'
        return output

    def to_dict(self, verbosity=1):
        return {'error': 'Not implemented for this record type.'}


class EdiTransactionRecord(EdiRecord):
    """Most of the records are parts of transactions."""

    transaction_sequence_number = EdiNumericField(size=8)
    record_sequence_number = EdiNumericField(size=8)

    def validate_sequences(self, transaction_sequence, record_sequence):
        """This is really a file-level validation."""

        if self.transaction_sequence_number != transaction_sequence:
            e = FileError(
                f'Wrong transaction sequence '
                f'{ self.transaction_sequence_number }, should be '
                f'{ transaction_sequence }')
            self.error('transaction_sequence_number', e)

        if self.record_sequence_number != record_sequence:
            e = FileError(
                f'Wrong transaction sequence '
                f'{ self.record_sequence_number }, should be '
                f'{ record_sequence }')
            self.error('record_sequence_number', e)

    def validate(self):
        """Validate the record, needed for subclasses."""
        pass

    def to_dict(self, verbosity=1):
        d = OrderedDict()
        for label, field in self.get_fields().items():

            # first three fields can be skipped
            if label in [
                'record_type',
                'transaction_sequence_number',
                'record_sequence_number'
            ] and label not in self.errors.keys():
                continue

            # constant fields can be skipper as well
            if isinstance(field, EdiConstantField):
                continue

            f = field.to_dict(record=self, label=label, verbosity=verbosity)
            if f is not None or verbosity > 1:
                d[label] = f
        return d


class EdiTRL(EdiRecord):
    """File trailer, minimal requirements."""
    record_type = EdiConstantField(size=3, constant='TRL', mandatory=True)
    group_count = EdiNumericField(size=5, mandatory=True)
    transaction_count = EdiNumericField(size=8, mandatory=True)
    record_count = EdiNumericField(size=8, mandatory=True)


class EdiGRH(EdiRecord):
    """Group header, minimal requirements."""
    record_type = EdiConstantField(size=3, constant='GRH', mandatory=True)
    transaction_type = EdiField(size=3, mandatory=True)
    group_code = EdiNumericField(size=5, mandatory=True)


class EdiGRT(EdiRecord):
    """Group trailer, minimal requirements."""
    record_type = EdiConstantField(size=3, constant='GRT', mandatory=True)
    group_code = EdiNumericField(size=5, mandatory=True)
    transaction_count = EdiNumericField(size=8, mandatory=True)
    record_count = EdiNumericField(size=8, mandatory=True)
