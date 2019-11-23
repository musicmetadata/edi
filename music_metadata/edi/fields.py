from weakref import WeakKeyDictionary
from .errors import *
import html

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
        self._valuedict[instance] = value

    def to_edi(self, value):
        """Return EDI format."""
        return str(value).ljust(self._size, ' ')

    def to_html(self, value, label='', verbose_value=None, error=None):
        """Create HTML representation for EDI, used in syntax highlighting"""
        if self:
            edi_value = self.to_edi(value)
        else:
            edi_value = value
        if verbose_value is None:
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
        try:
            value = int(value)
        except ValueError:
            raise RecordError(
                f'Value "{ value }" is not numeric')
        if not 0 <= value < 10 ** self._size:
            raise FieldError(
                f'Not between 0 "{ value }" and "{ 10 ** self._size - 1 }"')
        super().__set__(instance, value)

    def to_edi(self, value):
        """Return EDI format."""
        return str(value).rjust(self._size, '0')


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
            raise FieldError(
                f'Value must be "{ self._constant }", not "{ value }"')
        super().__set__(instance, value)

    def __get__(self, instance, owner=None):
        return self._constant

