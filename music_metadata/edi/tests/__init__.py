import os
import unittest

from music_metadata.edi.file import EdiFile, EdiGroup
from music_metadata.edi.records import *
from music_metadata.edi.transactions import EdiTransaction

FOLDER_PATH = os.path.dirname(os.path.realpath(__file__))
CWR2_PATH = os.path.join(FOLDER_PATH, 'CW190001MPC_000.V21')
CWR3_PATH = os.path.join(FOLDER_PATH, 'CW190008MPC_0000_V3-0-0.ISR')


class TestEdi(unittest.TestCase):

    def test_edifield(self):
        self.assertIsInstance(EdiRecord.record_type, EdiField)
        record = EdiRecord()
        field = list(record.fields)[0]
        self.assertEqual(record.to_edi(), '   ')
        self.assertIsNone(field.to_dict(record, verbosity=0))
        record.record_type = 'HDR'
        self.assertEqual(record.to_edi(), 'HDR')
        self.assertEqual(
            record.to_html(),
            '<span class="record record_type"><span class="field edifield '
            'object record_type" title ="record type: HDR">HDR</span><span '
            'class="field nonetype object " title =": "></span></span>')
        self.assertIn('error', record.to_dict())
        self.assertIsInstance(field.to_dict(record), dict)
        record.error('record_type', FieldError('testing'))
        self.assertEqual(
            record.to_html(),
            '<span class="record record_type invalid"><span class="field '
            'edifield object record_type invalid" title ="record type: '
            'HDR\nERROR: testing">HDR</span><span class="field nonetype '
            'object " title =": "></span></span>')
        self.assertIn('error', field.to_dict(record, verbosity=0))
        self.assertEqual(
            field.to_html('ABC'),
            '<span class="field edifield object record_type" title ="record '
            'type: ABC">ABC</span>')

    def test_edinumericfield(self):
        record = EdiTransactionRecord()
        record.transaction_sequence_number = '12345678'
        with self.assertRaises(RecordError):
            record.transaction_sequence_number = 'AAA'
        with self.assertRaises(FieldError):
            record.transaction_sequence_number = '123456789'

    def test_other_fields(self):

        with self.assertRaises(AttributeError):
            class Record(EdiTransactionRecord):
                bad_constant = EdiConstantField(size=5, constant='123')

        class Record(EdiTransactionRecord):
            filler = EdiConstantField(size=5)
            constant = EdiConstantField(size=5, constant='12345')
            bool = EdiBooleanField(mandatory=True)
            flag = EdiFlagField(mandatory=True)
            choice = EdiListField(size=2, choices=(
                ('A', 'Aa'), ('B', 'Bb'), ('AB', 'AaBb')))

        record = Record()
        record.record_type='ABC'
        record.bool = 'Y'
        record.choice = 'A '
        record.flag = 'U'

        self.assertEqual(record.to_edi(), 'ABC0000000000000000          YUA ')
        self.assertEqual(
            record.to_html(),
            '<span class="record record_type"><span class="field edifield '
            'object record_type" title ="record type: ABC">ABC</span><span '
            'class="field edinumericfield edifield '
            'transaction_sequence_number" title ="transaction sequence '
            'number: None">00000000</span><span class="field edinumericfield '
            'edifield record_sequence_number" title ="record sequence '
            'number: None">00000000</span><span class="field '
            'ediconstantfield edifield filler" title ="filler: None">     '
            '</span><span class="field ediconstantfield edifield constant" '
            'title ="constant: None">     </span><span class="field '
            'edibooleanfield edilistfield bool" title ="bool: '
            'Yes">Y</span><span class="field ediflagfield edilistfield flag" '
            'title ="flag: Unknown">U</span><span class="field edilistfield '
            'edifield choice" title ="choice: Aa">A </span><span '
            'class="field nonetype object " title =": "></span></span>')

        to_dict = record.to_dict(verbosity=1)
        should_return = OrderedDict([
            ('bool', OrderedDict([
                ('valid', True), ('value', True), ('verbose_value', 'Yes')])),
            ('choice', OrderedDict([
                ('valid', True), ('value', 'A'), ('verbose_value', 'Aa')]))])
        self.assertEqual(to_dict, should_return)

        record.get_fields()['flag']._mandatory = False
        record.flag = 'N'

        to_dict = record.to_dict(verbosity=0)
        should_return = OrderedDict([
            ('bool', True), ('flag', False), ('choice', 'A')])
        self.assertEqual(to_dict, should_return)

        # Test the exceptions, they must still change the values
        with self.assertRaises(FieldWarning):
            record.constant = '01234'
        self.assertEqual(record.constant, '01234')
        with self.assertRaises(FieldError):
            record.choice = 'C'
        self.assertEqual(record.constant, '01234')

    def test_edirecord(self):
        with self.assertRaises(FileError):
            EdiRecord('AA')

        class Record(EdiRecord):
            fil = EdiConstantField(size=1)
            num = EdiNumericField(size=4, mandatory=True)
            txt = EdiField(size=4, mandatory=False)

        record = Record('HDR 001')
        self.assertTrue(record.valid)
        self.assertIn('num', record.errors)
        self.assertIn('txt', record.errors)
        self.assertEqual(str(record), 'HDR 0001    ')

        # FieldWarning
        record = Record('HDRX001    ')
        self.assertTrue(record.valid)
        self.assertIn('fil', record.errors)
        self.assertEqual(str(record), 'HDRX0001    ')

        record = Record('HDR ')
        self.assertFalse(record.valid)
        self.assertIn('num', record.errors)
        self.assertEqual(str(record), 'HDR 0000    ')

        with self.assertRaises(AttributeError):
            record.warning('rest', FieldWarning('test'))

    def transaction_0(self, transaction):
        self.assertEqual(str(transaction), 'NWR00000000')
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if i == 0 and not record.valid:
                self.assertEqual(record.type, 'NWR')
            elif not record.valid:
                self.assertEqual(record.type, 'SPT')
                self.assertEqual(record.sequence, 2)
                self.assertIn('record_sequence_number', record.errors)
                self.assertIn('22',
                              str(record.errors.get('record_sequence_number')))
                self.assertIn('invalid', record.to_html())

    def transaction_1(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if i == 1 and not record.valid:
                self.assertEqual(record.type, '   ')
                self.assertIsNotNone(
                    record.errors.get('record_type'))
            elif not record.valid:
                self.assertEqual(record.type, 'SPT')
                self.assertEqual(record.sequence, 2)
                self.assertIn('000000X2', str(record.errors.get(None)))

    def transaction_2(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if i == 0 and not record.valid:
                for j, field in enumerate(record.fields):
                    d = field.to_dict(record, verbosity=j)
                    self.assertEqual(bool(j), isinstance(d, dict))
                    if j and d['valid'] is False:
                        self.assertIn('error', d)
                self.assertEqual(record.type, 'NWR')
                self.assertEqual(record.sequence, 0)
                self.assertIn(' 33', str(
                    record.errors.get('transaction_sequence_number')))

    def transaction_3(self, transaction):
        self.assertFalse(transaction.valid)
        for i, record in enumerate(transaction.records):
            self.assertEqual(record.sequence, i)
            if not record.valid:
                self.assertEqual(record.type, 'SPU')
                self.assertEqual(record.sequence, 1)
                self.assertIn('000000X3', str(record.errors.get(None)))

    def test_cwr21_processing(self):
        """
        Test EDI part of a CWR2.1 import.
        """

        with open(CWR2_PATH, 'rb') as f:
            e = EdiFile(f)
            header = e.get_header()
            self.assertEqual(header.record_type, 'HDR')
            self.assertEqual(header.get_transmission_dict(), {})
            self.assertIn('error', header.get_submitter_dict())
            for group in e.get_groups():
                self.assertEqual(str(group), 'NWR')

                transactions = group.get_transactions()

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

                for i, transaction in enumerate(transactions):
                    if i < 95:
                        self.assertTrue(transaction.valid)
                    else:
                        self.assertFalse(transaction.valid)

    def test_cwr21_processing_error_reporting(self):
        """
        Test EDI part of a CWR2.1 import.
        """

        with open(__file__, 'rb') as f:
            e = EdiFile(f)
            with self.assertRaises(FileError):
                list(e.get_groups())

        with open(CWR2_PATH, 'rb') as f:
            e = EdiFile(f)
            with self.assertWarns(DeprecationWarning):
                e.get_header()
            for group in e.list_groups():
                with self.assertWarns(DeprecationWarning):
                    f = group.get_file()
                self.assertEqual(e, f)
                with self.assertWarns(DeprecationWarning):
                    group.get_header()
                with self.assertRaises(RuntimeError):
                    # can not be run twice
                    list(group.get_transactions())
                with self.assertWarns(DeprecationWarning):
                    group.get_trailer()
            with self.assertWarns(DeprecationWarning):
                e.get_trailer()
        with open(CWR2_PATH, 'rb') as f:
            e = EdiFile(f)
            for group in e.get_groups():
                transactions = group.list_transactions()
                for transaction in transactions:
                    list(transaction.split_into_records())

    def test_cwr30_processing(self):
        """
        Test EDI part of a CWR3.0 import.
        """

        with open(CWR3_PATH, 'rb') as f:
            e = EdiFile(f)
            self.assertEqual(str(e), CWR3_PATH)
            self.assertEqual(e.header().record_type, 'HDR')
            for group in e.get_groups():
                self.assertEqual(group.header().transaction_type, 'ISR')
                self.assertEqual(group.file(), e)
                for transaction in group.get_transactions():
                    for record in transaction.records:
                        record.to_html()
                self.assertTrue(group.valid)
                self.assertTrue(e.valid)
                header = group.header()
                header.group_code += 1
                group.header(header=header)
                group.header(header.to_edi())
                # self.assertFalse(header.valid)
                # self.assertFalse(group.valid)
                trailer = group.trailer()
                trailer.group_code += 1
                trailer.transaction_count += 1
                group.trailer(trailer=trailer)
                # self.assertFalse(trailer.valid)
                group.trailer(trailer.to_edi())
                # self.assertFalse(group.valid)

    def test_new_file(self):
        """
        Test EDI generation.
        """
        EdiFile()
        group = EdiGroup('GHRWRK')
        self.assertIsNone(group.file())
        t = EdiTransaction('WRK')
        self.assertEqual(
            t.to_dict(), {
                'error': 'Not implemented for this file type.',
                'records': []})
        r = EdiTransactionRecord()
        r.record_type = t.type
        with self.assertRaises(ValueError):
            r.record_sequence_number = 'A'
        r.transaction_sequence_number = 0
        r.record_sequence_number = 0
        self.assertEqual(r.to_edi(), 'WRK0000000000000000')
        self.assertEqual(str(r), 'WRK0000000000000000')
