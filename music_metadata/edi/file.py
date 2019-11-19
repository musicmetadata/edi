import io


class EDIFile(io.TextIOWrapper):
    encoding = 'latin1'

