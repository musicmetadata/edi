import io


class EDIFile(io.TextIOWrapper):
    encoding = 'latin1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._header = self.get_header()
        self.reconfigure(encoding=self.get_encoding_from_header())

    def get_header(self):
        if hasattr(self, '_header'):
            return self._header
        position = self.tell()
        header = self.readline()
        self.seek(position)
        return header

    def get_encoding_from_header(self):
        return 'latin1'
