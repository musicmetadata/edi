import collections
from weakref import WeakKeyDictionary

class EDITransaction(object):
    def __init__(
            self, gtype, lines=None, sequence=None, reraise=True, *args, **kwargs):
        self.type = gtype
        self.sequence = sequence
        self.valid = True
        self.errors = []
        if lines:
            self.lines = lines
            self.records = list(self.split_into_records(reraise))
        else:
            self.lines = []
            self.records = []

    def __str__(self):
        return f'{self.type}{self.sequence:08d}'

    def split_into_records(self, reraise=True):
        expected_t_sequence = self.sequence or 0
        for expected_r_sequence, line in enumerate(
                self.lines.strip().split('\n')):
            try:
                t_sequence = line[3:11]
                try:
                    current_t_sequence = int(t_sequence)
                except ValueError:
                    raise ValueError(
                        f'Transaction sequence is not an integer {t_sequence}.')
                if current_t_sequence != expected_t_sequence:
                    raise ValueError(
                        f'Wrong transaction sequence {current_t_sequence}, should be '
                        f'{expected_t_sequence}')

                r_sequence = line[11:19]
                try:
                    current_r_sequence = int(r_sequence)
                except ValueError:
                    raise ValueError(
                        f'Record sequence is not an integer {r_sequence}.')
                if current_r_sequence != expected_r_sequence:
                    raise ValueError(
                        f'Wrong record sequence {current_r_sequence}, should be '
                        f'{expected_r_sequence} in transaction { self }')
                yield EDITransactionRecord(line)
            except ValueError as e:
                self.valid = False
                self.errors.append(e)
                record = EDIRecord(line)
                record.valid = False
                record.errors.append(e)
                if reraise:
                    raise
                yield record


class EDIField(object):
    def __init__(self, size):
        self._valuedict = WeakKeyDictionary()
        self._size = size

    def __get__(self, instance, owner=None):
        """Return object with proper value set."""
        if instance:
            return self._valuedict.get(instance)
        return self

    def __set__(self, instance, value):
        """Store the value."""
        self._valuedict[instance] = value

    def to_edi(self, value):
        return str(value).ljust(self._size, ' ')

    def to_html(self, value, class_atribute):
        edi_value = self.to_edi(value)
        return f'<span class="{ class_atribute }">{ edi_value }</span>'


class EDINumericField(EDIField):
    def __set__(self, instance, value):
        """Store the value."""
        try:
            value = int(value)
        except ValueError:
            raise ValueError(
                f'Value "{value}" is not numeric in "{instance.line}".')
        self._valuedict[instance] = value

    def to_edi(self, value):
        return str(value).rjust(self._size, '0')


class EDIRecordMeta(type):
    def __new__(cls, name, bases, classdict):
        classdict['_fields'] = collections.OrderedDict()
        for base in bases:
            if hasattr(base, '_fields'):
                classdict['_fields'].update(base._fields)
        for label, field in classdict.items():
            if isinstance(field, EDIField):
                classdict['_fields'][label] = field
        return super().__new__(cls, name, bases, classdict)


class EDIRecord(object, metaclass=EDIRecordMeta):
    def __init__(self, line=None, sequence=None):
        super().__init__()
        self.sequence = sequence
        self.line = line
        self.rest = None
        self.type = None
        self.valid = True
        self.errors = []
        if self.line and len(line)>3:
            self.split_into_fields()
            self.type = line[0:3]

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

    def to_html(self):
        classes = self.type
        if not self.valid:
            classes += ' invalid'
        output = f'<span class="{ classes }">'
        for label, field in self._fields.items():
            value = getattr(self, label)
            s = field.to_html(value, f'{ label }')
            output += s
        else:
            output += self.rest
        output += '</span>'
        return output

    def split_into_fields(self):
        pos = 0
        for label, field in self._fields.items():
            start = pos
            end = pos + field._size
            value = self.line[start:end]
            setattr(self, label, value)
            pos += field._size
        else:
            self.rest = self.line[pos:]

    record_type = EDIField(size=3)

    @property
    def fields(self):
        return self._fields.values()

    @property
    def labels(self):
        return self._fields.keys()


class EDITransactionRecord(EDIRecord):
    transaction_sequence_number = EDINumericField(size=8)
    record_sequence_number = EDINumericField(size=8)
