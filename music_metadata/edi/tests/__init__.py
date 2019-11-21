import unittest
from music_metadata.edi.file import EDIFile, EDIGroup
from music_metadata.edi.transaction import EDITransaction, EDITransactionRecord
import os
from io import BytesIO


FOLDER_PATH = os.path.dirname(os.path.realpath(__file__))
CWR2_PATH = os.path.join(FOLDER_PATH, 'CW190001MPC_000.V21')
CWR3_PATH = os.path.join(FOLDER_PATH, 'CW190008MPC_0000_V3-0-0.ISR')


class TestEDI(unittest.TestCase):

    def transaction_0(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if not record.valid:
                self.assertEqual(record.type, 'SPT')
                self.assertEqual(record.sequence, 2)
                self.assertIn('22', str(record.errors[0]))
                self.assertIn('invalid', record.to_html())

    def transaction_1(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if not record.valid:
                self.assertEqual(record.type, 'SPT')
                self.assertEqual(record.sequence, 2)
                self.assertIn('000000X2', str(record.errors[0]))

    def transaction_2(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if not record.valid:
                self.assertEqual(record.type, 'NWR')
                self.assertEqual(record.sequence, 0)
                self.assertIn(' 33', str(record.errors[0]))

    def transaction_3(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if not record.valid:
                self.assertEqual(record.type, 'SPU')
                self.assertEqual(record.sequence, 1)
                self.assertIn(' 000000X3', str(record.errors[0]))


    def test_cwr21_processing(self):
        """
        Test EDI part of a CWR2.1 import.
        """

        with open(CWR2_PATH, 'rb') as f:
            e = EDIFile(f)
            self.assertEqual(str(e), CWR2_PATH)
            self.assertEqual(e.get_header()[0:3], 'HDR')
            for group in e.get_groups():
                self.assertEqual(str(group), 'NWR')
                with self.assertRaises(ValueError) as ve:
                    list(group.get_transactions(reraise=True))
                self.assertIn(' 22', str(ve.exception))

                transactions = group.get_transactions(reraise=False)

                # Wrong record sequence, but still int
                transaction = next(transactions)
                self.transaction_0(transaction)

                # Wrong record sequence, not int
                transaction = next(transactions)
                self.transaction_1(transaction)

                # Wrong transaction sequence, int
                transaction = next(transactions)
                self.transaction_2(transaction)

                # Wrong transaction sequence, not int
                transaction = next(transactions)
                self.transaction_3(transaction)

                for transaction in transactions:
                    self.assertTrue(transaction.valid)

    def test_cwr30_processing(self):
        """
        Test EDI part of a CWR3.0 import.
        """

        with open(CWR3_PATH, 'rb') as f:
            e = EDIFile(f)
            self.assertEqual(str(e), CWR3_PATH)
            self.assertEqual(e.get_header()[0:3], 'HDR')
            for group in e.get_groups():
                for transaction in group.get_transactions():
                    for record in transaction.records:
                        record.to_html()

    def test_new_file(self):
        """
        Test EDI generation.
        """
        f = BytesIO(b'')
        EDIFile(f)
        EDIGroup(gtype='WRK')
        t = EDITransaction(gtype='WRK')
        r = EDITransactionRecord()
        r.record_type = t.type
        with self.assertRaises(ValueError):
            r.record_sequence_number = 'A'
        r.transaction_sequence_number = 0
        r.record_sequence_number = 0
        self.assertEqual(r.to_edi(), 'WRK0000000000000000')
        self.assertEqual(str(r), 'WRK0000000000000000')
        self.assertEqual(len(r.fields), len(r.labels))
