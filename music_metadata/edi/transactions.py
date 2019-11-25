from .errors import RecordError, FileError
from .records import EdiRecord, EdiTransactionRecord

class EdiTransaction(object):
    
    record_type = None
    record_classes = {}

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

    def get_record_class(self, record_type):
        return self.record_classes.get(
            record_type,
            EdiTransactionRecord)

    def split_into_records(self):
        expected_t_sequence = self.sequence or 0
        for expected_r_sequence, line in enumerate(
                self.lines.strip('\n').split('\n')):
            try:
                record = self.get_record_class(line[0:3])(line, expected_r_sequence)
            except (RecordError, FileError) as e:
                record = EdiRecord(line, expected_r_sequence)
                record.error(None, e)
                self.valid &= record.valid
                yield record
                continue

            record.validate_sequences(
                expected_t_sequence, expected_r_sequence)
            record.validate()
            self.valid &= record.valid
            yield record

