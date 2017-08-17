from ._Parser import Parser
# from ..NgramsExtractors import *
import sys
import csv
csv.field_size_limit(sys.maxsize)
import numpy as np
import os

class CSVParser(Parser):

    def parse(self, filebuf):

        print("CSV: parsing (assuming UTF-8 and LF line endings)")

        contents = filebuf.read().decode("UTF-8").split("\n")

        # Filter out empty lines
        contents = [line for line in contents if line.strip()]

        sample_size = 10
        sample_contents = contents[0:sample_size]

        hyperdata_list = []

        delimiters = ", \t;|:"

        # Compute frequency of each delimiter on each input line
        delimiters_freqs = {
            d: [line.count(d) for line in sample_contents]
            for d in delimiters
        }

        # Select delimiters with a standard deviation of zero, ie. delimiters
        # for which we have the same number of fields on each line
        selected_delimiters = [
            (d, np.sum(freqs))
            for d, freqs in delimiters_freqs.items()
            if any(freqs) and np.std(freqs) == 0
        ]

        if selected_delimiters:
            # Choose the delimiter with highest frequency amongst selected ones
            sorted_delimiters = sorted(selected_delimiters, key=lambda x: x[1])
            best_delimiter = sorted_delimiters[-1][0]
        else:
            raise ValueError("CSV: couldn't detect delimiter, bug or malformed data")

        print("CSV selected delimiter:", best_delimiter)

        # # = = = = [ First data coordinate ] = = = = #
        Coords = {
            "row": -1,
            "column": -1
        }

        reader = csv.reader(contents, delimiter=best_delimiter)

        for rownum, tokens in enumerate(reader):
            if rownum % 250 == 0:
                print("CSV row: ", rownum)
            joined_tokens = "".join (tokens)
            if Coords["row"]<0 and len( joined_tokens )>0 :
                Coords["row"] = rownum
                for columnum in range(len(tokens)):
                    t = tokens[columnum]
                    if len(t)>0:
                        Coords["column"] = columnum
                        break
        # # = = = = [ / First data coordinate ] = = = = #



        # # = = = = [ Setting Headers ] = = = = #
        Headers_Int2Str = {}
        reader = csv.reader(contents, delimiter=best_delimiter)
        for rownum, tokens in enumerate(reader):
            if rownum>=Coords["row"]:
                for columnum in range( Coords["column"],len(tokens) ):
                    t = tokens[columnum]
                    Headers_Int2Str[columnum] = t
                break
        # print("Headers_Int2Str")
        # print(Headers_Int2Str)
        # # = = = = [ / Setting Headers ] = = = = #
        # # OUTPUT example:
        # #  Headers_Int2Str = {
        # #     0: 'publication_date',
        # #      1: 'publication_month',
        # #      2: 'publication_second',
        # #      3: 'abstract'
        # #  }


        # # = = = = [ Reading the whole CSV and saving ] = = = = #
        hyperdata_list = []
        reader = csv.reader(contents, delimiter=best_delimiter)
        for rownum, tokens in enumerate(reader):
            if rownum>Coords["row"]:
                RecordDict = {}
                for columnum in range( Coords["column"],len(tokens) ):
                    data = tokens[columnum]
                    RecordDict[ Headers_Int2Str[columnum] ] = data
                if len(RecordDict.keys())>0:
                    hyperdata_list.append( RecordDict )
        # # = = = = [ / Reading the whole CSV and saving ] = = = = #

        return hyperdata_list
