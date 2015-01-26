# ****************************
# *****  Medline Fetcher *****
# ****************************

# MEDLINE USER REQUIREMENT : Run retrieval scripts on weekends or between 9 pm and 5 am Eastern Time weekdays
import sys
if sys.version_info >= (3, 0): from urllib.request import urlopen
else: from urllib import urlopen
import os
import time
# import libxml2
from lxml import etree

class MedlineFetcher:

    def __init__(self):
        self.pubMedEutilsURL = 'http://www.ncbi.nlm.nih.gov/entrez/eutils'
        self.pubMedDB = 'Pubmed'
        self.reportType = 'medline'
        self.personalpath_mainPath = 'MedLine/'
        if not os.path.isdir(self.personalpath_mainPath):
            os.makedirs(self.personalpath_mainPath)
            print ('Created directory ' + self.personalpath_mainPath)

    # Return the:
    # - count = 
    # - queryKey = 
    # - webEnv = 
    def medlineEsearch(self , query):

        print ("MedlineFetcher::medlineEsearch :")

        "Get number of results for query 'query' in variable 'count'"
        "Get also 'queryKey' and 'webEnv', which are used by function 'medlineEfetch'"
        
        query = query.replace(' ', '%20')
            
        eSearch = '%s/esearch.fcgi?db=%s&retmax=1&usehistory=y&term=%s' %(self.pubMedEutilsURL, self.pubMedDB, query)
        eSearchResult = urlopen(eSearch)
        data = eSearchResult.read()

        root = etree.XML(data)

        findcount = etree.XPath("/eSearchResult/Count/text()")
        count = findcount(root)[0]
        
        findquerykey = etree.XPath("/eSearchResult/QueryKey/text()")
        queryKey = findquerykey(root)[0]

        findwebenv = etree.XPath("/eSearchResult/WebEnv/text()")
        webEnv = findwebenv(root)[0]

        # doc = libxml2.parseDoc(data)
        # count = doc.xpathEval('eSearchResult/Count/text()')[0]
        # queryKey = doc.xpathEval('eSearchResult/QueryKey/text()')[0]
        # webEnv = doc.xpathEval('eSearchResult/WebEnv/text()')[0]
        # print count, queryKey, webEnv
        values = { "count": int(str(count)), "queryKey": queryKey , "webEnv":webEnv }
        return values


    # RETMAX:
    # Total number of UIDs from the retrieved set to be shown in the XML output (default=20)
    # maximum of 100,000 records
    def medlineEfetchRAW( self , fullquery):
        

        query = fullquery["string"]
        retmax = fullquery["retmax"]
        count = fullquery["count"]
        queryKey = fullquery["queryKey"]
        webEnv = fullquery["webEnv"]

        print ("MedlineFetcher::medlineEfetchRAW :")

        "Fetch medline result for query 'query', saving results to file every 'retmax' articles"

        queryNoSpace = query.replace(' ', '') # No space in directory and file names, avoids stupid errors
        

        # pubmedqueryfolder = personalpath.pubMedAbstractsPath + 'Pubmed_' + queryNoSpace
        # if not os.path.isdir(pubmedqueryfolder):
        #     os.makedirs(pubmedqueryfolder)

        pubMedResultFileName = self.personalpath_mainPath + 'Pubmed_' + queryNoSpace + '.xml'
        pubMedResultFile = open(pubMedResultFileName, 'w')
        

        print ('Query "' , query , '"\t:\t' , count , ' results')
        print ('Starting fetching at ' , time.asctime(time.localtime()) )

        retstart = 0
        # while(retstart < count):
        eFetch = '%s/efetch.fcgi?email=youremail@example.org&rettype=%s&retmode=xml&retstart=%s&retmax=%s&db=%s&query_key=%s&WebEnv=%s' %(self.pubMedEutilsURL, self.reportType, retstart, retmax, self.pubMedDB, queryKey, webEnv)
        return eFetch
        #     if sys.version_info >= (3, 0): pubMedResultFile.write(eFetchResult.read().decode('utf-8'))
        #     else: pubMedResultFile.write(eFetchResult.read())
        #     retstart += retmax
        #     break # you shall not pass !!

        # pubMedResultFile.close()
        # print ('Fetching for query ' , query , ' finished at ' , time.asctime(time.localtime()) )
        # print (retmax , ' results written to file ' , pubMedResultFileName , '\n' )
        # print("------------------------------------------")
        # return ["everything","ok"]



    # GLOBALLIMIT:
    # I will retrieve this exact amount of publications.
    # The publications per year i'll retrieve per year will be = (k/N)*GlobalLimit <- i'll use this as RETMAX
    # - k : Number of publications of x year (according to pubmed)
    # - N : Sum of every k belonging to {X} (total number of pubs according to pubmed)
    # - GlobalLimit : Number of publications i want.
    def serialFetcher(self , yearsNumber , query, globalLimit):

        N = 0

        print ("MedlineFetcher::serialFetcher :")
        thequeries = []
        for i in range(yearsNumber):
            year = str(2015 - i)
            print ('YEAR ' + year)
            print ('---------\n')
            # medlineEfetch(str(year) + '[dp] '+query , 20000)
            # medlineEfetchRAW(str(year) + '[dp] '+query , retmax=300)
            pubmedquery = str(year) + '[dp] '+query
            globalresults = self.medlineEsearch(pubmedquery)
            N+=globalresults["count"]
            querymetadata = { 
                "string": pubmedquery , 
                "count": globalresults["count"] , 
                "queryKey":globalresults["queryKey"] , 
                "webEnv":globalresults["webEnv"] , 
                "retmax":0 
            }
            thequeries.append ( querymetadata )

        print("Total Number:", N,"publications")
        print("And i want just:",globalLimit,"publications")
        print("---------------------------------------\n")

        for query in thequeries:
            k = query["count"]
            percentage = k/float(N)
            retmax_forthisyear = int(round(globalLimit*percentage))
            query["retmax"] = retmax_forthisyear
            # self.medlineEfetchRAW( query )

        print ('Done !')
        return thequeries



# serialFetcher(yearsNumber=3, 'microbiota' , globalLimit=100 )
# query = str(2015)+ '[dp] '+'microbiota'
# medlineEsearch( query )

# 
