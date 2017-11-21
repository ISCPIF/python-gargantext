from ._Parser import Parser
import pandas
import io


class CSVParser(Parser):
    ENCODING = "utf-8"

    def open(self, file):
        f = super(CSVParser, self).open(file)

        if isinstance(file, str) and file.endswith('.zip'):
            return f

        return io.TextIOWrapper(f, encoding=self.ENCODING)

    def parse(self, fp=None):
        fp = fp or self._file
        df = pandas.read_csv(fp, dtype=object, skip_blank_lines=True, sep=None,
                                 na_values=[], keep_default_na=False)

        # Return a generator of dictionaries with column labels as keys,
        # filtering out empty rows
        for i, fields in enumerate(df.itertuples(index=False)):
            if i % 500 == 0:
                print("CSV: parsing row #%s..." % (i+1))

            # See https://docs.python.org/3/library/collections.html#collections.somenamedtuple._asdict
            yield fields._asdict()
