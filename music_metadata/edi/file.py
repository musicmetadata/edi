import io


class EDIFile(io.TextIOWrapper):
    encoding = 'latin1'

    def __init__(self):
        super().__init__()
        self._header = self.get_header()

    def get_header(self):
        if hasattr(self, '_header'):
            return self._header
        position = self.tell()
        header = self.readline()
        self.seek(position)
        return header