import fitz
import re

# this is how a block looks like: {'number': 0, 'type': 0, 'bbox': (211.48800659179688, 96.52021026611328, 399.89349365234375, 118.91744995117188), 'lines': [{'spans': [{'size': 17.21540069580078, 'flags': 20, 'font': 'NimbusRomNo9L-Medi', 'color': 0, 'ascender': 0.9599999785423279, 'descender': -0.3409999907016754, 'text': 'Attention Is All You Need', 'origin': (211.48800659179688, 113.0469970703125), 'bbox': (211.48800659179688, 96.52021026611328, 399.89349365234375, 118.91744995117188)}], 'wmode': 0, 'dir': (1.0, 0.0), 'bbox': (211.48800659179688, 96.52021026611328, 399.89349365234375, 118.91744995117188)}]}

def flags_decomposer(flags):
    """Make font flags human readable."""
    l = []
    if flags & 2 ** 0:
        l.append("superscript")
    if flags & 2 ** 1:
        l.append("italic")
    if flags & 2 ** 2:
        l.append("serifed")
    else:
        l.append("sans")
    if flags & 2 ** 3:
        l.append("monospaced")
    else:
        l.append("proportional")
    if flags & 2 ** 4:
        l.append("bold")
    return ", ".join(l)

# regex function that returns true if a string looks like a word of a sentence
def is_word(string):
    if len(string)>4 and len(string)<50:
        # print(len(string))
        return True
    else:
        return False

def get_outline(pdf_path):

    doc = fitz.open(pdf_path)

    # Get the fontsizes with frequency
    fontsizes = {}
    flags = {}

    # Loop through the pages
    for page in doc:
        # Get the text blocks
        blocks = page.get_text("dict")["blocks"]
        # Loop through the blocks
        for block in blocks:
            try:
                # Get the font size
                size = block['lines'][0]['spans'][0]['size']
                flag = block['lines'][0]['spans'][0]['flags']
                # Print the font size
                if size in fontsizes:
                    fontsizes[size]+=1
                else:
                    fontsizes[size]=1

                if flag in flags:
                    flags[flag]+=1
                else:
                    flags[flag]=1
            except:
                continue

    # Get the most common font size
    most_common_fontsize = max(fontsizes, key=fontsizes.get)
    # print(most_common_fontsize)

    # Get the most common flag
    most_common_flag = max(flags, key=flags.get)
    # print(most_common_flag)

    # get the second most common flag
    # flags.pop(most_common_flag)
    # second_most_common_flag = max(flags, key=flags.get)
    # print(second_most_common_flag)

    # # print lines with not the most common fontsize
    # for page in doc:
    #     # Get the text blocks
    #     blocks = page.get_text("dict")["blocks"]
    #     # Loop through the blocks
    #     for block in blocks:
    #         try:
    #             # Get the font size
    #             size = block['lines'][0]['spans'][0]['size']
    #             # Print the font size
    #             if size>most_common_fontsize:
    #                 print(block['lines'][0]['spans'][0]['text'])
    #         except:
    #             continue
    
    # print lines with not the most common flag
    for page in doc:
        # Get the text blocks
        blocks = page.get_text("dict")["blocks"]
        # Loop through the blocks
        for block in blocks:
            try:
                # Get the font size
                flag = block['lines'][0]['spans'][0]['flags']
                # Print the font size
                if flag!=most_common_flag:
                    # print(f"FLAG: {flag}", block['lines'][0]['spans'][0]['text'])
                    if is_word(block['lines'][0]['spans'][0]['text']):
                        print(block['lines'][0]['spans'][0]['text'])
                        print(flags_decomposer(flag))
                        # pass
            except:
                continue


if __name__ == "__main__":

    get_outline("transformers.pdf")
        