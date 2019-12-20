"""
Music Metadata - EDI is a base library for several EDI-based formats by CISAC,
most notably Common Works Registration (CWR) and Common Royalty Distribution
(CRD).

This file contains the file and group handling."""

import io
import re
from weakref import ref

from .records import *
from .transactions import EdiTransaction

RE_GROUPS = re.compile(
    r'(?P<lines>^GRH(?P<gtype>.{3})(?P<sequence>\d{5}).*?^GRT(\3).*?$)',
    re.M | re.S)
RE_TRL = re.compile(r'^TRL.*?$', re.M | re.S)
RE_GRT = re.compile(r'^GRT.*?$', re.M | re.S)


class EdiGroup(object):
    header_class = EdiGRH
    trailer_class = EdiGRT
    transaction_classes = [EdiTransaction]

    def __init__(self, gtype, lines=None, sequence=None, *args, **kwargs):
        self.type = gtype
        self.errors = []
        self.valid = True
        self.sequence = sequence
        self.transaction_count = 0
        self.record_count = 2
        if lines:
            self.lines = lines
        else:
            self.lines = ''
        self.get_header()
        self.get_trailer()

    def __str__(self):
        return self.type

    def get_file(self):
        return None

    def get_header(self):
        if hasattr(self, '_header'):
            return self._header
        if self.lines:
            self._header = self.header_class(self.lines.split('\n')[0])
            if self._header.group_code != self.sequence:
                e = FileError(
                    f'Wrong group ID: {self._header.group_code} instead of '
                    f'{self.sequence}')
                self.errors.append(e)
                self._header.error('group_code', e)
                self.get_file().valid = False
            self.valid &= self._header.valid
            return self._header
        return None

    def get_trailer(self):
        if hasattr(self, '_trailer'):
            return self._trailer
        if self.lines:
            grts = list(re.findall(RE_GRT, self.lines))
            if len(grts) == 0:
                raise FileError('Group trailer record (GRT) not found')
            if len(grts) > 1:
                raise FileError('Multiple group trailer records (GRT) found')
            grt = grts[0]
            self._trailer = self.trailer_class(grt)
            self.valid &= self._trailer.valid
            if self.sequence != self._trailer.group_code:
                e = FileError(
                    f'Wrong group ID: {self._trailer.group_code} instead of'
                    f'{self.sequence}')
                self.errors.append(e)
                self._trailer.error('group_code', e)
                self.get_file().valid = False
            return self._trailer
        return None

    def get_transaction_class(self):
        for transaction_class in self.transaction_classes:
            if self.type == transaction_class.record_type:
                return transaction_class
        return EdiTransaction

    def get_transactions(self):
        sequence = 0
        pattern = re.compile(
            r'(^{0}.*?(?=^GRT|^{0}))'.format(self.type), re.S | re.M)
        try:
            for transaction_lines in re.findall(pattern, self.lines):
                transaction_class = self.get_transaction_class()
                transaction = transaction_class(
                    self.type, transaction_lines, sequence)
                for error in transaction.errors:
                    if isinstance(error, FileError):
                        self.valid = False
                        self.errors.append(error)
                        self.get_file().valid = False
                        self.get_file().file_errors.append(error)
                        break
                yield transaction
                sequence += 1
                self.transaction_count += 1
                self.record_count += len(transaction.records)
            else:
                trailer = self.get_trailer()
                if self.transaction_count != trailer.transaction_count:
                    self.valid = False
                    self.get_file().valid = False
                    e = FileError(
                        f'Wrong transaction count in GRT: '
                        f'{trailer.transaction_count}, counted '
                        f'{self.transaction_count}')
                    self.errors.append(e)
                    trailer.error('transaction_count', e)
                if self.record_count != trailer.record_count:
                    self.valid = False
                    self.get_file().valid = False
                    e = FileError(
                        f'Wrong record count in GRT: '
                        f'{trailer.record_count}, counted '
                        f'{self.record_count}')
                    self.errors.append(e)
                    trailer.error('record_count', e)
        except FileError as e:
            self.valid = False
            self.errors.append(e)
            raise

    def list_transactions(self):
        return list(self.get_transactions())


class EdiFile(io.TextIOWrapper):
    header_class = EdiRecord
    trailer_class = EdiTRL
    group_class = EdiGroup

    @classmethod
    def is_my_header(cls, hdr):
        return False

    def __new__(cls, buffer=None, *args, **kwargs):
        if buffer:
            hdr = buffer.readline()
            for child_class in cls.__subclasses__():
                if child_class.is_my_header(hdr):
                    return super().__new__(child_class, buffer, *args,
                                           **kwargs)
        return super().__new__(cls, buffer, *args, **kwargs)

    def __init__(self, buffer=None, encoding='latin1', *args, **kwargs):
        if buffer is None:
            existing_file = False
            buffer = io.BytesIO()
        else:
            existing_file = True
        super().__init__(buffer, encoding=encoding, *args, **kwargs)
        self.valid = True
        self.file_errors = []
        self.group_count = 0
        self.transaction_count = 0
        self.record_count = 2
        if existing_file:
            self.get_header()
            self.get_trailer()
            self.reconfigure(encoding=self.get_encoding_from_header())

    def __str__(self):
        return self.name

    def get_header(self):
        if hasattr(self, '_header'):
            return self._header
        position = self.tell()
        self.seek(0)
        self._header = self.header_class(self.readline())
        self.seek(position)
        return self._header

    def get_trailer(self):
        if hasattr(self, '_trailer'):
            return self._trailer
        position = self.tell()
        self.seek(0)
        trls = list(re.findall(RE_TRL, self.read()))
        if len(trls) == 0:
            raise FileError('File trailer record (TRL) not found')
        if len(trls) > 1:
            raise FileError('Multiple trailer records (TRL) found')
        self.seek(position)
        trl = trls[0]
        self._trailer = self.trailer_class(trl)
        return self._trailer

    def get_groups(self):
        expected_sequence = 0
        record_count = 2
        transaction_count = 0
        for r in re.finditer(RE_GROUPS, self.read()):
            expected_sequence += 1
            d = r.groupdict()
            group = self.group_class(d['gtype'], d['lines'], expected_sequence)
            self.group_count += 1
            self.valid &= group.valid
            trailer = group.get_trailer()
            record_count += trailer.record_count
            transaction_count += trailer.transaction_count
            self.valid &= group.valid
            group.get_file = ref(self)
            yield group
        else:
            if expected_sequence == 0:
                e = FileError('No valid groups found in the file.')
                self.valid = False
                self.file_errors.append(e)

            trailer = self.get_trailer()

            if expected_sequence != trailer.group_count:
                self.valid = False
                e = FileError(
                    'Wrong group count in TRL: '
                    f'{trailer.group_count}, '
                    f'counted {expected_sequence}')
                self.file_errors.append(e)
                trailer.error('group_count', e)

            self.transaction_count = transaction_count
            if transaction_count != trailer.transaction_count:
                self.valid = False
                e = FileError(
                    'Wrong transaction count in TRL: '
                    f'{trailer.transaction_count}, '
                    f'GRTs say {transaction_count}')
                self.file_errors.append(e)
                trailer.error('transaction_count', e)

            self.record_count = record_count
            if record_count != trailer.record_count:
                self.valid = False
                e = FileError(
                    'Wrong record count in TRL: '
                    f'{trailer.record_count}, '
                    f'GRTs say {record_count}')
                self.file_errors.append(e)
                trailer.error('record_count', e)

    def list_groups(self):
        return list(self.get_groups())

    def get_encoding_from_header(self):
        return 'latin1'
