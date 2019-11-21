import io
import re
from .transaction import EDITransaction


RE_GROUPS = re.compile(
    r'(?P<lines>^GRH(?P<gtype>.{3})(?P<sequence>\d{5}).*?^GRT(\3).*?$)', re.M | re.S)


class EDIFile(io.TextIOWrapper):
    encoding = 'latin1'

    def __init__(self, buffer, *args, **kwargs):
        super().__init__(buffer, *args, **kwargs)
        self._header = self.get_header()
        self.reconfigure(encoding=self.get_encoding_from_header())

    def __str__(self):
        return self.name

    def get_header(self):
        if hasattr(self, '_header'):
            return self._header
        position = self.tell()
        header = self.readline()
        self.seek(position)
        return header

    def get_groups(self, reraise=True):
        try:
            expected_sequence = 0
            for r in re.finditer(RE_GROUPS, self.read()):
                expected_sequence += 1
                d = r.groupdict()
                sequence = d['sequence']
                try:
                    current_sequence = int(sequence)
                except ValueError:
                    raise ValueError(
                        f'Group sequence is not an integer { sequence }.')
                if current_sequence != expected_sequence:
                    raise ValueError(
                        f'Wrong group sequence {current_sequence}, should be '
                        f'{expected_sequence}')
                d['sequence'] = current_sequence
                yield EDIGroup(**d)
        except ValueError as e:
            self.valid = False
            self.errors.append(e)
            if reraise:
                raise

    def get_encoding_from_header(self):
        return 'latin1'

    def get_version_from_header(self):
        return None


class EDIGroup(object):
    def __init__(self, gtype, lines=None, sequence=None, *args, **kwargs):
        self.type = gtype
        self.sequence = sequence
        self.errors = []
        self.valid = True
        if lines:
            self.lines = lines
        else:
            self.lines = ''

    def __str__(self):
        return self.type

    def get_transactions(self, reraise=True):
        sequence = 0
        pattern = re.compile(
            r'(^{0}.*?(?=^GRT|{0}))'.format(self.type), re.S | re.M)
        for transaction_lines in re.findall(pattern, self.lines):
            yield EDITransaction(
                self.type, transaction_lines, sequence, reraise=reraise)
            sequence += 1

    def get_transactions_with_errors(self):
        return self.get_transactions(reraise=False)
