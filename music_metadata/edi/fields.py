"""
Music Metadata - EDI is a base library for several EDI-based formats by CISAC,
most notably Common Works Registration (CWR) and Common Royalty Distribution (CRD).

This file contains field descriptors."""


from weakref import WeakKeyDictionary
from .errors import *
import html
from collections import OrderedDict


class EdiField(object):
    """Base class for all EDI Fields, also used for alphanumeric fields.

    Alphanumeric fields are left-aligned, space-padded and default is blank."""

    verbose_type = 'Alphanumeric'

    def __init__(self, size, mandatory=None, *args, **kwargs):
        self._size = size
        self._mandatory = mandatory

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance:
            return getattr(self, self._name)
        return self

    def __set__(self, instance, value):
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                value = None
        if value is None and self._mandatory:
            raise FieldError('Value is mandatory')
        setattr(self, self._name, value)

    def to_edi(self, value):
        """Return EDI format."""
        if value is None:
            value = ''
        return str(value).ljust(self._size, ' ')

    def verbose(self, value):
        """Return verbose (human-readable) value"""
        return value

    def to_html(self, value, label='', error=None):
        """Create HTML representation for EDI, used in syntax highlighting"""
        if self:
            edi_value = self.to_edi(value)
            verbose_value = self.verbose(value)
        else:
            edi_value = value
            verbose_value = value
        descriptive_label = label.replace('_', ' ')
        classes = self.__class__.__name__ + ' '
        classes += ' '.join(c.__name__ for c in self.__class__.__bases__)
        classes = classes.lower()
        if error:
            error = html.escape(str(error))
            return (
                f'<span class="field { classes } { label } invalid" '
                f'title ="{ descriptive_label }: { verbose_value }\n'
                f'ERROR: { error }">{ edi_value }</span>')
        else:
            return (
                f'<span class="field { classes } { label }" title ="{ descriptive_label }:'
                f' { verbose_value }">{ edi_value }</span>')

    def to_dict(self, record, label=None, verbosity=1):
        """Create the dictionary with the value and additional data."""
        if label is None:
            label = self._name
        value = getattr(record, label)
        valid = record.valid or label not in record.errors
        if value is None and valid and verbosity <= 1:
            return None
        if value and valid and verbosity == 0:
            return value
        d = OrderedDict()
        if verbosity > 1:
            d['type'] = self.verbose_type
        d['valid'] = valid
        if not valid:
            d['error'] = str(record.errors.get(label))
        d['value'] = value
        return d


class EdiNumericField(EdiField):
    """Numeric fields are right-aligned, zero-padded and default is filled with zeros."""

    verbose_type = 'Numeric field'

    def __set__(self, instance, value):
        if value is not None:
            try:
                value = int(value)
            except ValueError:
                raise RecordError(
                    f'Value "{ value }" is not numeric')
            if not 0 <= value < 10 ** self._size:
                raise FieldError(
                    f'Not between 0 "{ value }" and "{ 10 ** self._size - 1 }"'
                )
        super().__set__(instance, value)

    def to_edi(self, value):
        """Return EDI format."""
        return str(value or 0).rjust(self._size, '0')


class EdiConstantField(EdiField):
    """Constant fields have a preset value.

    If value is specified, it must match the length of the field."""

    def __init__(self, size, constant=None, *args, **kwargs):
        if constant:
            if len(constant) == size:
                self._constant = constant
            else:
                raise AttributeError(
                    f'Value "{ value }" is not { size } characters long.')
        else:
            self._constant = ' ' * size
        super().__init__(size, *args, **kwargs)

    def __set__(self, instance, value):
        if value != self._constant:
            super().__set__(instance, value)
            raise FieldWarning(
                f'Value must be "{ self._constant }", not "{ value }"')
        super().__set__(instance, value)


class EdiListField(EdiField):
    """List field is basically an immutable key-value list with short keys."""

    verbose_type = 'List field'

    def __init__(self, size, choices, *args, **kwargs):
        self._choices = OrderedDict(choices)
        super().__init__(size, *args, **kwargs)

    def __set__(self, instance, value):
        if isinstance(value, str):
            value = value.strip()
        if value and value not in self._choices.keys():
            super().__set__(instance, value)
            raise FieldError(
                'Value must be one of ' 
                f'''\"{ '", "'.join(self._choices.keys()) }\"''')
        super().__set__(instance, value)

    def verbose(self, value):
        return self._choices.get(value) or value

    def to_dict(self, record, label=None, verbosity=1):
        d = super().to_dict(record, label, verbosity)
        if d is not isinstance(d, dict):
            return d
        value = d.get('value')
        name = self.verbose(value)
        d['verbose_value'] = name
        return d


class EdiFlagField(EdiListField):
    """Flag field is basically a null-boolean."""

    verbose_type = 'Flag field'

    def __init__(self, *args, **kwargs):
        size = 1
        choices = ((True, 'Yes'), (False, 'No'), (None, 'Unknown'))
        super().__init__(size=size, choices=choices, *args, **kwargs)

    def __set__(self, instance, value):
        if self._mandatory and value == 'U':
            # Unknown resolves to None, so super() makes no sense
            self._valuedict[instance] = None
            return
        value = dict(
            (('Y', True), ('N', False), ('U', None), (' ', None))
        ).get(value, value)
        super().__set__(instance, value)

    def to_edi(self, value):
        value = dict((
            (True, 'Y'), (False, 'N'), (None, 'U' if self._mandatory else ' ')
        )).get(value, ' ')
        return value


class EdiBooleanField(EdiListField):
    """Boolean field."""

    verbose_type = 'Boolean field'

    def __init__(self, *args, **kwargs):
        size = 1
        choices = ((True, 'Yes'), (False, 'No'))
        super().__init__(size=size, choices=choices, *args, **kwargs)

    def __set__(self, instance, value):
        value = dict(
            (('Y', True), ('N', False), (' ', None))
        ).get(value, value)
        super().__set__(instance, value)

    def to_edi(self, value):
        value = dict(
            ((True, 'Y'), (False, 'N'), (None, ' '))
        ).get(value, ' ')
        return value

