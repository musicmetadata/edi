"""
Music Metadata - EDI is a base library for several EDI-based formats by CISAC,
most notably Common Works Registration (CWR) and Common Royalty Distribution
(CRD).

This file contains the file and group handling."""

import io
# import re
from weakref import ref

from .records import *
from .transactions import EdiTransaction
import warnings


class EdiGroup(object):
    """Parent class for all EDI Group types.

    It is NOT an abstract class, separation down to transaction level is
    independant of the type of EDI.

    """

    header_class = EdiGRH
    trailer_class = EdiGRT
    transaction_classes = [EdiTransaction]

    def __init__(self, header_line=None):
        self._header = self.header_class(header_line)
        self.valid = True
        self.errors = []
        self.transaction_count = 0
        self.record_count = 2  # header and trailer not counted

    @property
    def type(self):
        return self._header.transaction_type

    @property
    def sequence(self):
        return self._header.group_code

    def __str__(self):
        return str(self.type)

    def file(self, f=None):
        """Set file as weak reference."""
        if f:
            self._file = ref(f)()
        return self._file

    def get_transactions(self):
        """Iterate through transactions."""

        f = self.file()
        sequence = 0
        current_transaction_lines = []

        if f.current_group != self:
            raise RuntimeError(
                'get_transactions was already run for this group.')
        # current line should be the first line of the first transaction
        while f.current_line:
            if f.current_line[0:3] == 'GRT':
                if current_transaction_lines:
                    transaction_class = self.get_transaction_class()
                    transaction = transaction_class(
                        str(self.type), current_transaction_lines, sequence)
                    self.transaction_count += 1
                    yield transaction
                    sequence += 1
                # add the trailer and process transaction errors
                trailer = self.trailer(f.current_line)
                for error in transaction.errors:
                    if isinstance(error, FileError):
                        self.valid = False
                        self.errors.append(error)
                        self.file().valid = False
                        self.file().file_errors.append(error)
                trailer = self.trailer()
                if self.transaction_count != trailer.transaction_count:
                    self.valid = False
                    self.file().valid = False
                    e = FileError(
                        f'Wrong transaction count in GRT: '
                        f'{trailer.transaction_count}, counted '
                        f'{self.transaction_count}')
                    self.errors.append(e)
                    trailer.error('transaction_count', e)
                if self.record_count != trailer.record_count:
                    self.valid = False
                    self.file().valid = False
                    e = FileError(
                        f'Wrong record count in GRT: '
                        f'{trailer.record_count}, counted '
                        f'{self.record_count}')
                    self.errors.append(e)
                    trailer.error('record_count', e)

                # mark as not being processed
                f.current_group = None
                return
            if f.current_line[0:3] == str(self.type):
                if current_transaction_lines:
                    transaction_class = self.get_transaction_class()
                    transaction = transaction_class(
                        str(self.type), current_transaction_lines, sequence)
                    self.transaction_count += 1
                    yield transaction
                    sequence += 1
                    current_transaction_lines = []
            current_transaction_lines.append(f.current_line)
            self.record_count += 1
            f.readline()

    def get_file(self):
        warnings.warn('Use EdiGroup.file() instead', DeprecationWarning)
        return self.file()

    def header(self, header_line=None, header=None):
        if header:
            self.header_line = ''
            self._header = header
            self.header_line = header.to_edi()
        elif header_line:
            self.header_line = header_line
            self._header = self.header_class(self.header_line)
        elif self._header:
            return self._header
        elif self.header_line:
            self._header = self.header_class(self.header_line)
        else:
            return None
        if self.sequence != self._header.group_code:
            e = FileError(
                f'Wrong group ID: {self._header.group_code} instead of'
                f'{self.sequence}')
            self.errors.append(e)
            self._header.error('group_code', e)
            file = self.file()
            if file:
                file.valid = False
        self.valid &= self._header.valid
        return self._header

    def get_header(self):
        warnings.warn('Use EdiGroup.header() instead', DeprecationWarning)
        return self.header()

    def trailer(self, trailer_line=None, trailer=None):
        if trailer:
            self.trailer_line = ''
            self._trailer = trailer
        elif trailer_line:
            self.trailer_line = trailer_line
            self._trailer = self.trailer_class(self.trailer_line)
        elif self._trailer:
            return self._trailer
        elif self.trailer_line:
            self._trailer = self.trailer_class(self.trailer_line)
        else:
            return None
        if self.sequence != self._trailer.group_code:
            e = FileError(
                f'Wrong group ID: {self._trailer.group_code} instead of'
                f'{self.sequence}')
            self.errors.append(e)
            self._trailer.error('group_code', e)
            file = self.file()
            if file:
                file.valid = False
        self.valid &= self._trailer.valid
        return self._trailer

    def get_trailer(self):
        warnings.warn('Use EdiGroup.trailer() instead', DeprecationWarning)
        return self.trailer()

    def get_transaction_class(self):
        for transaction_class in self.transaction_classes:
            if self.type == transaction_class.record_type:
                return transaction_class
        return EdiTransaction

    # def get_transactions(self):
    #     sequence = 0
    #     pattern = re.compile(
    #         r'(^{0}.*?)(?=^{0}|\Z)'.format(self.type), re.S | re.M)
    #     try:
    #         for transaction_lines in re.findall(pattern, self.transaction_lines):
    #             transaction_class = self.get_transaction_class()
    #             transaction = transaction_class(
    #                 self.type, transaction_lines, sequence)
    #             for error in transaction.errors:
    #                 if isinstance(error, FileError):
    #                     self.valid = False
    #                     self.errors.append(error)
    #                     self.file().valid = False
    #                     self.file().file_errors.append(error)
    #                     break
    #             yield transaction
    #             sequence += 1
    #             self.transaction_count += 1
    #             self.record_count += len(transaction.records)
    #         else:
    #             trailer = self.trailer()
    #             if self.transaction_count != trailer.transaction_count:
    #                 self.valid = False
    #                 self.file().valid = False
    #                 e = FileError(
    #                     f'Wrong transaction count in GRT: '
    #                     f'{trailer.transaction_count}, counted '
    #                     f'{self.transaction_count}')
    #                 self.errors.append(e)
    #                 trailer.error('transaction_count', e)
    #             if self.record_count != trailer.record_count:
    #                 self.valid = False
    #                 self.file().valid = False
    #                 e = FileError(
    #                     f'Wrong record count in GRT: '
    #                     f'{trailer.record_count}, counted '
    #                     f'{self.record_count}')
    #                 self.errors.append(e)
    #                 trailer.error('record_count', e)
    #     except FileError as e:
    #         self.valid = False
    #         self.errors.append(e)
    #         raise

    def list_transactions(self):
        return list(self.get_transactions())


class EdiFile(io.TextIOWrapper):
    header_class = EdiHDR
    trailer_class = EdiTRL
    group_class = EdiGroup

    @classmethod
    def is_my_header(cls, hdr):
        return False

    def readline(self):
        if self.seekable() and self.position > self.tell():
            self.seek(self.position)
        line = super().readline().strip('\n')
        self.current_line = line
        if self.seekable():
            self.position = self.tell()
        return line

    # def __new__(cls, buffer=None, *args, **kwargs):
    #     if buffer:
    #         hdr = buffer.readline().decode('latin1')
    #         for child_class in cls.__subclasses__():
    #             if child_class.is_my_header(hdr):
    #                 return super().__new__(child_class, buffer, *args,
    #                                        **kwargs)
    #     else:
    #         hdr = None
    #     obj = super().__new__(cls, buffer, *args, **kwargs)
    #     obj.header_line = hdr
    #     return obj

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
        if self.seekable():
            self.position = self.tell()
        self.current_line = self.header_line = self.readline()
        self._header = None
        self._trailer = None
        self.current_group = None
        if existing_file:
            for child_class in self.__class__.__subclasses__():
                if child_class.is_my_header(self.header_line):
                    self.__class__ = child_class
            self.header()

    def __str__(self):
        return self.name

    def header(self):
        if self._header:
            return self._header
        self._header = self.header_class(self.header_line)
        # self.reconfigure(encoding=self.get_encoding_from_header())
        return self._header

    def get_header(self):
        return self.header()

    def trailer(self):
        if self._trailer:
            return self._trailer
        self._trailer = self.trailer_class(self.trailer_line)

        return self._trailer

    def get_trailer(self):
        return self.trailer()

    def get_groups(self):
        expected_sequence = 0
        self.readline()
        while self.current_line:
            # End of file, break
            if self.current_line[0:3] == 'TRL':
                self.trailer_line = self.current_line
                trailer = self.trailer()
                if self.transaction_count != trailer.transaction_count:
                    self.valid = False
                    e = FileError(
                        f'Wrong transaction count in TRL: '
                        f'{trailer.transaction_count}, counted '
                        f'{self.transaction_count}')
                    self.file_errors.append(e)
                    trailer.error('transaction_count', e)
                if self.record_count != trailer.record_count:
                    self.valid = False
                    e = FileError(
                        f'Wrong record count in TRL: '
                        f'{trailer.record_count}, counted '
                        f'{self.record_count}')
                    self.file_errors.append(e)
                    trailer.error('record_count', e)
                if expected_sequence != trailer.group_count:
                    self.valid = False
                    e = FileError(
                        'Wrong group count in TRL: '
                        f'{trailer.group_count}, '
                        f'counted {expected_sequence}')
                    self.file_errors.append(e)
                    trailer.error('group_count', e)

                self.readline()
                break

            # Next group
            expected_sequence += 1

            # The next line must be GRH, if not, it is a bad file.
            if self.current_line[0:3] != 'GRH':
                e = FileError('Group header missing for group {}'.format(
                    expected_sequence))
                self.valid = False
                self.file_errors.append(e)
                raise Exception('not right: {}'.format(self.current_line))
                break

            # create the new group, consume this line
            group = self.group_class(self.current_line)
            self.readline()
            # set file to the group (it's a weak reference)
            group.file(self)

            # EDIGroup.get_transactions will unset this variable
            self.current_group = group

            # check sequence
            if group.sequence != expected_sequence:
                e = FileError('Group sequence mismatch {} vs {}'.format(
                    expected_sequence, group.sequence))
                self.valid = False
                self.file_errors.append(e)

            yield group
            self.transaction_count += group.transaction_count
            self.record_count += group.record_count

            # lines must be read, if not read already
            if self.current_group:
                for t in self.current_group.get_transactions():
                    pass

            self.readline()
        else:
            e = FileError('File trailer missing')
            self.valid = False
            self.file_errors.append(e)

        # for r in re.finditer(RE_GROUPS, self.read()):
        #     expected_sequence += 1
        #     d = r.groupdict()
        #     group = self.group_class(
        #         d['gtype'], d['header'], d['trailer'], d['lines'],
        #         expected_sequence)
        #     self.group_count += 1
        #     self.valid &= group.valid
        #     trailer = group.trailer()
        #     record_count += trailer.record_count
        #     transaction_count += trailer.transaction_count
        #     self.valid &= group.valid
        #     group.file(self)
        #     yield group
        # else:
        #     if expected_sequence == 0:
        #         e = FileError('No valid groups found in the file.')
        #         self.valid = False
        #         self.file_errors.append(e)
        #
        #     trailer = self.get_trailer()
        #
        #     if expected_sequence != trailer.group_count:
        #         self.valid = False
        #         e = FileError(
        #             'Wrong group count in TRL: '
        #             f'{trailer.group_count}, '
        #             f'counted {expected_sequence}')
        #         self.file_errors.append(e)
        #         trailer.error('group_count', e)
        #
        #     self.transaction_count = transaction_count
        #     if transaction_count != trailer.transaction_count:
        #         self.valid = False
        #         e = FileError(
        #             'Wrong transaction count in TRL: '
        #             f'{trailer.transaction_count}, '
        #             f'GRTs say {transaction_count}')
        #         self.file_errors.append(e)
        #         trailer.error('transaction_count', e)
        #
        #     self.record_count = record_count
        #     if record_count != trailer.record_count:
        #         self.valid = False
        #         e = FileError(
        #             'Wrong record count in TRL: '
        #             f'{trailer.record_count}, '
        #             f'GRTs say {record_count}')
        #         self.file_errors.append(e)
        #         trailer.error('record_count', e)

    def list_groups(self):
        return list(self.get_groups())

    def get_encoding_from_header(self):
        return 'latin1'
