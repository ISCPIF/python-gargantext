#!/usr/bin/env python
# *coding:Utf8*
""" 
Pubmed Database parser
__author__ : http://alexandre.delanoe.org
__licence__ : GPL version 3.0+
__DATE__ : 2014
__VERSION__ : 0.1
"""

import datetime
import sys, string, codecs
from lxml import etree

from documents.models import Document

class Pubmed() :
    """
    Pubmed, Medline corpus parser
    """
    def __init__(self) :
        """
        See Corpus class which declares what a corpus is
        """
        Corpus.__init__(self)
        self.bdd = "Medline"

    
#    class Article(Text):
#        def __init__(self) :
#            Text.__init__(self)

    
    def parse(self, file, bdd="PUBMED") :
        """
        The file needed is the file to be parsed in xml format.
        The bdd is the filed of BDD-SOURCE.
        """
        document = {}
        source = open(file, 'r')
        
        parser = etree.XMLParser(resolve_entities=False,recover=True)
        xml = etree.parse(source, parser=parser)

        xml_docs = xml.findall('PubmedArticle/MedlineCitation')

        for xml_doc in xml_docs:
            year = int(xml_doc.find('DateCreated/Year').text)
            month = int(xml_doc.find('DateCreated/Month').text)
            day = int(xml_doc.find('DateCreated/Day').text)
            
            self.Article.date = datetime.date(year, month, day)
            self.Article.journal = xml_doc.find('Article/Journal/Title').text
            self.Article.title = xml_doc.find('Article/ArticleTitle').text
            self.texts.append(self.Article)

#            if xmlDoc.find("PubmedArticle") is not None :
#                print ok

    def add(self, file):
        self.parse(file)

def demo(file):
    data = Pubmed()
    #data.parse(file='../data/pubmed/pubmed_result.xml')
    data.parse(file)
    print(data.texts[0])
#    for i in data.keys():
#        print i

if __name__ == "__main__" :
    try:
        demo()
    except Exception as error :
        print(error)

#
#<PubmedArticle>
#    <MedlineCitation Status="Publisher" Owner="NLM">
#        <PMID Version="1">24363549</PMID>
#        <DateCreated>
#            <Year>2013</Year>
#            <Month>12</Month>
#            <Day>23</Day>
#        </DateCreated>
#        <Article PubModel="Print-Electronic">
#            <Journal>
#                <ISSN IssnType="Print">1080-7039</ISSN>
#                <JournalIssue CitedMedium="Print">
#                    <Volume>20</Volume>
#                    <Issue>2</Issue>
#                    <PubDate>
#                        <Year>2014</Year>
#                        <Month>Feb</Month>
#                    </PubDate>
#                </JournalIssue>
#                <Title>Human and ecological risk assessment : HERA</Title>
#                <ISOAbbreviation>Hum Ecol Risk Assess</ISOAbbreviation>
#            </Journal>
#            <ArticleTitle>A Causal Analysis of Observed Declines in Managed Honey Bees (Apis mellifera).</ArticleTitle>
#            <Pagination>
#                <MedlinePgn>566-591</MedlinePgn>
#            </Pagination>
#            <Abstract>
#                <AbstractText NlmCategory="UNLABELLED">The European honey bee (Apis mellifera) is a highly valuable, semi-free-ranging managed agricultural species. While the number of managed hives has been increasing, declines in overwinter survival, and the onset of colony collapse disorder in 2006, precipitated a large amount of research on bees' health in an effort to isolate the causative factors. A workshop was convened during which bee experts were introduced to a formal causal analysis approach to compare 39 candidate causes against specified criteria to evaluate their relationship to the reduced overwinter survivability observed since 2006 of commercial bees used in the California almond industry. Candidate causes were categorized as probable, possible, or unlikely; several candidate causes were categorized as indeterminate due to lack of information. Due to time limitations, a full causal analysis was not completed at the workshop. In this article, examples are provided to illustrate the process and provide preliminary findings, using three candidate causes. Varroa mites plus viruses were judged to be a &quot;probable cause&quot; of the reduced survival, while nutrient deficiency was judged to be a &quot;possible cause.&quot; Neonicotinoid pesticides were judged to be &quot;unlikely&quot; as the sole cause of this reduced survival, although they could possibly be a contributing factor.</AbstractText>
#            </Abstract>
#            <AuthorList>
#                <Author>
#                    <LastName>Staveley</LastName>
#                    <ForeName>Jane P</ForeName>
#                    <Initials>JP</Initials>
#                    <Affiliation>Exponent, Alexandria, VA, USA.</Affiliation>
#                </Author>
#                <Author>
#                    <LastName>Law</LastName>
#                    <ForeName>Sheryl A</ForeName>
#                    <Initials>SA</Initials>
#                    <Affiliation>Exponent, Alexandria, VA, USA.</Affiliation>
#                </Author>
#                <Author>
#                    <LastName>Fairbrother</LastName>
#                    <ForeName>Anne</ForeName>
#                    <Initials>A</Initials>
#                    <Affiliation>Exponent, Bellevue, WA, USA.</Affiliation>
#                </Author>
#                <Author>
#                    <LastName>Menzie</LastName>
#                    <ForeName>Charles A</ForeName>
#                    <Initials>CA</Initials>
#                    <Affiliation>Exponent, Alexandria, VA, USA.</Affiliation>
#                </Author>
#            </AuthorList>
#            <Language>ENG</Language>
#            <PublicationTypeList>
#                <PublicationType>JOURNAL ARTICLE</PublicationType>
#            </PublicationTypeList>
#            <ArticleDate DateType="Electronic">
#                <Year>2013</Year>
#                <Month>11</Month>
#                <Day>25</Day>
#            </ArticleDate>
#        </Article>
#        <MedlineJournalInfo>
#            <MedlineTA>Hum Ecol Risk Assess</MedlineTA>
#            <NlmUniqueID>9513572</NlmUniqueID>
#            <ISSNLinking>1080-7039</ISSNLinking>
#        </MedlineJournalInfo>
#        <KeywordList Owner="NOTNLM">
#            <Keyword MajorTopicYN="N">Varroa</Keyword>
#            <Keyword MajorTopicYN="N">causal analysis</Keyword>
#            <Keyword MajorTopicYN="N">honey bees</Keyword>
#            <Keyword MajorTopicYN="N">neonicotinoids</Keyword>
#        </KeywordList>
#    </MedlineCitation>
#    <PubmedData>
#        <History>
#            <PubMedPubDate PubStatus="received">
#                <Year>2013</Year>
#                <Month>7</Month>
#                <Day>8</Day>
#            </PubMedPubDate>
#            <PubMedPubDate PubStatus="accepted">
#                <Year>2013</Year>
#                <Month>7</Month>
#                <Day>23</Day>
#            </PubMedPubDate>
#            <PubMedPubDate PubStatus="epublish">
#                <Year>2013</Year>
#                <Month>11</Month>
#                <Day>25</Day>
#            </PubMedPubDate>
#            <PubMedPubDate PubStatus="entrez">
#                <Year>2013</Year>
#                <Month>12</Month>
#                <Day>24</Day>
#                <Hour>6</Hour>
#                <Minute>0</Minute>
#            </PubMedPubDate>
#            <PubMedPubDate PubStatus="pubmed">
#                <Year>2013</Year>
#                <Month>12</Month>
#                <Day>24</Day>
#                <Hour>6</Hour>
#                <Minute>0</Minute>
#            </PubMedPubDate>
#            <PubMedPubDate PubStatus="medline">
#                <Year>2013</Year>
#                <Month>12</Month>
#                <Day>24</Day>
#                <Hour>6</Hour>
#                <Minute>0</Minute>
#            </PubMedPubDate>
#        </History>
#        <PublicationStatus>ppublish</PublicationStatus>
#        <ArticleIdList>
#            <ArticleId IdType="doi">10.1080/10807039.2013.831263</ArticleId>
#            <ArticleId IdType="pubmed">24363549</ArticleId>
#            <ArticleId IdType="pmc">PMC3869053</ArticleId>
#        </ArticleIdList>
#        <?pmcsd?>
#    </PubmedData>
#</PubmedArticle>
#

