from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import string, io, requests, re

def preprocess(listoflines):

    listtoreturn = []
    
    for line in listoflines:
        
        # remove leading and trailing whitespace
        line = line.strip()

        # replace \n with space
        line = line.replace('\n', ' ')

        # removing double spaces
        line = re.sub(' +', ' ', line)

        templine = line

        # remove all punctuation
        for char in string.punctuation:
            templine = templine.replace(char, '')

        # if the line is empty, skip it
        if templine == '':
            continue

        # if the line is a single alphabet character, skip it
        if len(templine) == 1 and templine.isalpha():
            continue

        # if the firse word is a number, add it to the list to return
        if templine.split(' ')[0].isdigit():
            listtoreturn.append('<h>::'+line)
        else:
            listtoreturn.append(line)
    
    return listtoreturn

def extract_text_from_pdf(pdf_path):
    output_string = StringIO()

    with open(pdf_path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

    text = output_string.getvalue()

    # close open handles
    device.close()
    output_string.close()

    if text:
        return text

def extract_text_from_pdf_url(pdf_url):
    output_string = StringIO()
    try:
        response = requests.get(pdf_url)
        in_file = io.BytesIO(response.content)

        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

        text = output_string.getvalue()

        # close open handles
        device.close()
        output_string.close()

        if text:
            return text
    except Exception as e:
        print("Error: ", e)
    
def parse_pdf_from_url(pdf_url):

    response = requests.get(pdf_url)
    in_file = io.BytesIO(response.content)

    parser = PDFParser(in_file)
    doc = PDFDocument(parser)
    
    return doc

def make_chunks(listoflines):
    
    minlen = 64
    maxwords = 128

    chunks = []
    
    nextchunk = ''

    lastlinewashead = False
    
    for i in range(len(listoflines)):

        line = listoflines[i]

#         # if the reference section is reached, break the loop
#         if line.lower().startswith('references'):
#             if nextchunk != '':
#                 chunks.append(nextchunk)
#                 nextchunk = ''
#             return chunks
        
        if line.startswith('<h>::'):

            # if the next chunk starts with 'references', and then the next line is a number, 1. or 1), or 1-1, or [1], then just break the loop
#             if line.lower().startswith('references'):
#                 if nextchunk != '':
#                     if len(nextchunk) > minlen:
#                         chunks.append(nextchunk)
#                         nextchunk = ''
#                 return chunks
            
            # if the next chunk is not empty, and the last line was not a header, then add the next chunk to the list of chunks
            if nextchunk != '' and not lastlinewashead:

                if len(nextchunk) > minlen:
                    chunks.append(nextchunk)
                    nextchunk = ''

            elif lastlinewashead:
                nextchunk = ''

            nextchunk += line[5:] + '\n'
            lastlinewashead = True
            continue

        else:
            
            if len(nextchunk.split(' ')) > maxwords*2.5:
                for i in range(0, len(nextchunk.split(' ')), maxwords):
                    if i+maxwords>len(nextchunk.split(' ')):
                        chunks.append(' '.join(nextchunk.split(' ')[i:]))
                    else:
                        chunks.append(' '.join(nextchunk.split(' ')[i:i+maxwords]))
                nextchunk = ''
            elif len(nextchunk.split(' ')) > maxwords*1.1: # 10% tolerance
                chunks.append(nextchunk)
                nextchunk = ''

            nextchunk += line + '\n'
            lastlinewashead = False
        
    if nextchunk != '':
        if len(nextchunk) > minlen:
            chunks.append(nextchunk)

    return chunks

def pdftochunks(pdf_path):
    
    text = extract_text_from_pdf(pdf_path)
    listoflines = text.split('\n\n')
    listoflines = preprocess(listoflines)
    chunks = make_chunks(listoflines)
    
    return chunks


def pdfdchunks_file(file):
    output_string = io.StringIO()
    in_file = io.BytesIO(file.read())
    parser = PDFParser(in_file)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())

    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)

    text = output_string.getvalue()

    # close open handles
    device.close()
    output_string.close()

    if text:
        listoflines = text.split('\n\n')
        listoflines = preprocess(listoflines)
        chunks = make_chunks(listoflines)
        return chunks

def pdftochunks_url(pdf_url):
    text = extract_text_from_pdf_url(pdf_url)
    listoflines = text.split('\n\n')
    listoflines = preprocess(listoflines)
    chunks = make_chunks(listoflines)
    return chunks