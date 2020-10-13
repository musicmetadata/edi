"""
Music Metadata - EDI is a base library for several EDI-based formats by CISAC,
most notably Common Works Registration (CWR) and Common Royalty Distribution
(CRD).

This file contains the transaction skeleton."""

from .errors import FileError, RecordError
from .records import EdiRecord, EdiTransactionRecord


class EdiTransaction(object):
    """Base class for all transactions."""

    record_type = None
    record_classes = {}

    def __init__(self, gtype, lines=None, sequence=None, *args, **kwargs):
        self.type = gtype
        self.sequence = sequence
        self.valid = True
        self.errors = []  # Transaction-level errors
        if lines:
            self.lines = lines
            self.records = list(self.split_into_records())
            self.validate_record_order()
        else:
            self.lines = []
            self.records = []

    def __str__(self):
        return f'{self.type}{self.sequence:08d}'

    def error(self, error, record=None, fieldname=None):
        """Add an error, and invalidate."""
        if record is not None and error not in record.errors:
            record.error(fieldname, error)
        self.errors.append(error)
        self.valid = False

    def validate_record_order(self):
        return

    def get_record_class(self, record_type):
        return self.record_classes.get(record_type, EdiTransactionRecord)

    def split_into_records(self):
        expected_t_sequence = self.sequence or 0
        for expected_r_sequence, line in enumerate(self.lines):
            try:
                Record = self.get_record_class(line[0:3])
                record = Record(line, expected_r_sequence)
            except (RecordError, FileError) as e:
                record = EdiTransactionRecord(line, expected_r_sequence)
                record.error(None, e)
                self.valid &= record.valid
                yield record
                continue

            record.validate_sequences(expected_t_sequence, expected_r_sequence)
            record.validate()
            self.valid &= record.valid
            for error in record.errors.values():
                if isinstance(error, FileError):
                    self.error(error, record)
                    break
            yield record

    def to_dict(self, verbosity=1):
        return {
            'error': 'Not implemented for this file type.',
            'records': [r.to_edi() for r in self.records]}
