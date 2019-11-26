from weakref import WeakKeyDictionary
from .errors import *
import html
from collections import OrderedDict


class EdiField(object):
    """Base class for all EDI Fields"""

    def __init__(self, size, mandatory=None, *args, **kwargs):
        self._valuedict = WeakKeyDictionary()
        self._size = size
        self._mandatory = mandatory

    def __get__(self, instance, owner=None):
        if instance:
            return self._valuedict.get(instance)
        return self

    def __set__(self, instance, value):
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                value = None
        if value is None and self._mandatory:
            raise FieldError('Value is mandatory')
        self._valuedict[instance] = value

    def to_edi(self, value):
        """Return EDI format."""
        if value is None:
            value = ''
        return str(value).ljust(self._size, ' ')

    def verbose(self, value):
        """REturn verbose (human-readable) value"""
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
        if error:
            error = html.escape(str(error))
            return (
                f'<span class="field { label } invalid" '
                f'title ="{ descriptive_label }: { verbose_value }\n'
                f'ERROR: { error }">{ edi_value }</span>')
        else:
            return (
                f'<span class="field { label }" title ="{ descriptive_label }:'
                f' { verbose_value }">{ edi_value }</span>')


class EdiNumericField(EdiField):
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
    def __init__(self, size, constant=None, *args, **kwargs):
        if constant:
            if len(constant) == size:
                self._constant = constant
            else:
                f'Value "{ value }" is not { size } characters long.'
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


class EdiFlagField(EdiListField):
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

