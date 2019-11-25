import collections
from .fields import *


class EdiRecordMeta(type):
    """Meta class for EdiRecord"""
    def __new__(cls, name, bases, classdict):
        classdict['_fields'] = collections.OrderedDict()
        for base in bases:
            if hasattr(base, '_fields'):
                classdict['_fields'].update(base._fields)
        for label, field in classdict.items():
            if isinstance(field, EdiField):
                classdict['_fields'][label] = field
        return super().__new__(cls, name, bases, classdict)


class EdiRecord(object, metaclass=EdiRecordMeta):

    record_type = EdiField(size=3)

    def __init__(self, line=None, sequence=None):
        super().__init__()
        self.sequence = sequence
        self.line = line
        self.rest = ''
        self.type = None
        self.valid = True
        self.errors = {}
        if self.line:
            if len(self.line) > 3:
                self.split_into_fields()
                self.type = line[0:3]
            else:
                raise FileError(f'Record too short: { line }')

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
        if field and field not in self.labels:
            raise AttributeError(f'No such field { field } in { self.labels }')
        self.errors[field] = error

    def error(self, field, error):
        self.valid = False
        self.warning(field, error)


    def split_into_fields(self):
        pos = 0
        specified_length = 0
        actual_length = len(self.line)
        for field in self.fields:
            specified_length += field._size
        if specified_length > actual_length:
            self.line = self.line.ljust(specified_length)
        for label, field in self._fields.items():
            start = pos
            end = pos + field._size
            pos += field._size
            value = self.line[start:end]
            if start < actual_length < end:
                self.warning(label, FieldError('Field truncated'))
            elif end > actual_length:
                if field._mandatory:
                    self.error(label, RecordError('Mandatory field missing'))
                else:
                    self.warning(label, FieldError(
                        'Field missing at the end of the line.'))
            try:
                setattr(self, label, value)
            except FieldError as e:
                self.error(label, e)
            except (RecordError, FileError) as e:
                self.error(label, e)
                raise
        else:
            self.rest = self.line[pos:]

    @property
    def fields(self):
        return self._fields.values()

    @property
    def labels(self):
        return self._fields.keys()

    def to_html(self):
        classes = f'record { self.type }'
        if not self.valid:
            classes += ' invalid'
        output = f'<span class="{ classes }">'
        for label, field in self._fields.items():
            value = getattr(self, label)
            s = field.to_html(
                value, f'{ label }', self.errors.get(label))
            output += s
        else:
            output += EdiField.to_html(
                None, self.rest, label='', error=self.errors.get(None))
        output += '</span>'
        return output


class EdiTransactionRecord(EdiRecord):
    transaction_sequence_number = EdiNumericField(size=8)
    record_sequence_number = EdiNumericField(size=8)

    def validate_sequences(self, transaction_sequence, record_sequence):
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
        pass


class EdiTRL(EdiRecord):
    record_type = EdiConstantField(size=3, constant='TRL', mandatory=True)
    group_count = EdiNumericField(size=5, mandatory=True)
    transaction_count = EdiNumericField(size=8, mandatory=True)
    record_count = EdiNumericField(size=8, mandatory=True)


class EdiGRH(EdiRecord):
    record_type = EdiConstantField(size=3, constant='GRH', mandatory=True)
    transaction_type = EdiField(size=3, mandatory=True)
    group_id = EdiNumericField(size=5, mandatory=True)


class EdiGRT(EdiRecord):
    record_type = EdiConstantField(size=3, constant='GRT', mandatory=True)
    group_id = EdiNumericField(size=5, mandatory=True)
    transaction_count = EdiNumericField(size=8, mandatory=True)
    record_count = EdiNumericField(size=8, mandatory=True)
