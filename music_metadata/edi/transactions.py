from .errors import *
from .records import EdiRecord, EdiTransactionRecord

class EdiTransaction(object):
    def __init__(
            self, gtype, lines=None, sequence=None, *args, **kwargs):
        self.type = gtype
        self.sequence = sequence
        self.valid = True
        self.errors = []  # Transaction-level errors
        if lines:
            self.lines = lines
            self.records = list(self.split_into_records())
        else:
            self.lines = []
            self.records = []

    def __str__(self):
        return f'{self.type}{self.sequence:08d}'

    def split_into_records(self):
        expected_t_sequence = self.sequence or 0
        for expected_r_sequence, line in enumerate(
                self.lines.strip().split('\n')):
            try:
                record = EdiTransactionRecord(line, expected_r_sequence)
            except (RecordError, FileError) as e:
                record = EdiRecord(line, expected_r_sequence)
                record.error(None, e)
                self.valid &= record.valid
                yield record
                continue

            record.validate_sequences(
                expected_t_sequence, expected_r_sequence)
            self.valid &= record.valid
            yield record

