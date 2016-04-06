from ._Parser import Parser
# from ..NgramsExtractors import *
import sys
import csv
csv.field_size_limit(sys.maxsize)
import numpy as np
import os

class CSVParser(Parser):

    def CSVsample( self, small_contents , delim) :
        reader = csv.reader(small_contents, delimiter=delim)

        Freqs = []
        for row in reader:
            Freqs.append(len(row))

        return Freqs


    def parse(self, filename):

        print("CSV: parsing (assuming UTF-8 and LF line endings)")

        contents = filename.read().decode("UTF-8").split("\n")

        sample_size = 10
        sample_contents = contents[0:sample_size]

        hyperdata_list = []

        # # = = = = [ Getting delimiters frequency ] = = = = #
        PossibleDelimiters = [ ',',' ','\t', ';', '|', ':' ]
        AllDelimiters = {}
        for delim in PossibleDelimiters:
            AllDelimiters[delim] = self.CSVsample( sample_contents , delim )
        # # = = = = [ / Getting delimiters frequency ] = = = = #
        # # OUTPUT example:
        # #  AllDelimiters = {
        # #   '\t': [1, 1, 1, 1, 1],
        # #   ' ': [1, 13, 261, 348, 330],
        # #   ',': [15, 15, 15, 15, 15],
        # #   ';': [1, 1, 1, 1, 1],
        # #   '|': [1, 1, 1, 1, 1]
        # #  }

        # # = = = = [ Stand.Dev=0 & Sum of delimiters ] = = = = #
        Delimiters = []
        for d in AllDelimiters:
            freqs = AllDelimiters[d]
            suma = np.sum( freqs )
            if suma >0:
                std = np.std( freqs )
                # print [ d , suma , len(freqs) , std]
                if std == 0:
                    Delimiters.append ( [ d , suma , len(freqs) , std] )
        # # = = = = [ / Stand.Dev=0 & Sum of delimiters ] = = = = #
        # # OUTPUT example:
        # #  Delimiters = [
        # #     ['\t', 5, 5, 0.0],
        # #     [',', 75, 5, 0.0],
        # #     ['|', 5, 5, 0.0]
        # #  ]


        # # = = = = [ Delimiter selection ] = = = = #
        Sorted_Delims = sorted(Delimiters, key=lambda x: x[1], reverse=True)
        HighestDelim = Sorted_Delims[0][0]
        # HighestDelim = ","
        print("CSV selected delimiter:",[HighestDelim])
        # # = = = = [ / Delimiter selection ] = = = = #


        # # = = = = [ First data coordinate ] = = = = #
        Coords = {
            "row": -1,
            "column": -1
        }

        reader = csv.reader(contents, delimiter=HighestDelim)

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
        reader = csv.reader(contents, delimiter=HighestDelim)
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
        reader = csv.reader(contents, delimiter=HighestDelim)
        for rownum, tokens in enumerate(reader):
            if rownum>Coords["row"]:
                RecordDict = {}
                for columnum in range( Coords["column"],len(tokens) ):
                    data = tokens[columnum]
                    RecordDict[ Headers_Int2Str[columnum] ] = data
                hyperdata_list.append( RecordDict )
        # # = = = = [ / Reading the whole CSV and saving ] = = = = #

        return hyperdata_list
