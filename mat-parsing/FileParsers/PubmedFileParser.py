from FileParser import FileParser


class PubmedFileParser(FileParser):
    
    def parse(self):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False,recover=True)
        xml = etree.parse(self._file, parser=xml_parser)
        # find all the abstracts
        xml_docs = xml.findall('PubmedArticle/MedlineCitation')
        for xml_doc in xml_docs:
            metadata = {}
            date_year = int(xml_doc.find('DateCreated/Year').text)
            date_month = int(xml_doc.find('DateCreated/Month').text)
            date_day = int(xml_doc.find('DateCreated/Day').text)
            metadata["date"] = datetime.date(year, month, day)
            metadata["journal"] = xml_doc.find('Article/Journal/Title').text
            metadata["title"] = xml_doc.find('Article/ArticleTitle').text
            contents = 