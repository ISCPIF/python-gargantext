from django.db import transaction
from .FileParser import FileParser
# from ..NgramsExtractors import *
import sys
import csv
csv.field_size_limit(sys.maxsize)
import numpy as np
import os

class CSVParser(FileParser):

    def CSVsample( self, filename , delim) :
        ifile  = open( filename, "r" )
        reader = csv.reader(ifile, delimiter=delim)

        Freqs = []
        for row in reader:
            Freqs.append(len(row))


        ifile.close()
        return Freqs

    
    def _parse(self, filename):

        sample_size = 10
        sample_file = filename.replace(".csv","_sample.csv")

        hyperdata_list = []

        command_for_sample = "cat '"+filename+"' | head -n "+str(sample_size)+" > '"+sample_file+"'"
        os.system(command_for_sample) # you just created a  *_sample.csv

        # # = = = = [ Getting delimiters frequency ] = = = = #
        PossibleDelimiters = [ ',',' ','\t', ';', '|', ':' ]
        AllDelimiters = {}
        for delim in PossibleDelimiters:
            AllDelimiters[delim] = self.CSVsample( sample_file , delim ) 
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
        # print("selected delimiter:",[HighestDelim]
        # print
        # # = = = = [ / Delimiter selection ] = = = = #




        # # = = = = [ First data coordinate ] = = = = #
        Coords = {
            "row": -1,
            "column": -1
        }

        ifile  = open( sample_file, "r" )
        reader = csv.reader(ifile, delimiter=HighestDelim)

        for rownum, tokens in enumerate(reader):
            joined_tokens = "".join (tokens)
            if Coords["row"]<0 and len( joined_tokens )>0 :
                Coords["row"] = rownum
                for columnum in range(len(tokens)):
                    t = tokens[columnum]
                    if len(t)>0:
                        Coords["column"] = columnum
                        break
        ifile.close()
        # # = = = = [ / First data coordinate ] = = = = #



        # # = = = = [ Setting Headers ] = = = = #
        Headers_Int2Str = {}
        ifile  = open( sample_file, "r" )
        reader = csv.reader(ifile, delimiter=HighestDelim)
        for rownum, tokens in enumerate(reader):
            if rownum>=Coords["row"]:
                for columnum in range( Coords["column"],len(tokens) ):
                    t = tokens[columnum]
                    Headers_Int2Str[columnum] = t
                break
        ifile.close()
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
        ifile  = open( filename, "r" )
        reader = csv.reader(ifile, delimiter=HighestDelim)
        for rownum, tokens in enumerate(reader):
            if rownum>Coords["row"]:
                RecordDict = {}
                for columnum in range( Coords["column"],len(tokens) ):
                    data = tokens[columnum]
                    RecordDict[ Headers_Int2Str[columnum] ] = data
                hyperdata_list.append( RecordDict )
        ifile.close()
        # # = = = = [ / Reading the whole CSV and saving ] = = = = #

        return hyperdata_list
