import re

def check_references(chunk):
    # Define regular expressions for various reference formats
    apa_regex = r'\[[0-9]+\]\s[A-Za-z0-9,:\s]+[0-9]+\.\s'
    mla_regex = r'\[[0-9]+\]\s[A-Za-z0-9,:\s]+\. [A-Za-z]+\s?[0-9]+\.'
    chicago_regex = r'\[[0-9]+\]\s[A-Za-z0-9,:\s]+\.[\sA-Za-z]+:[\sA-Za-z]+\s?[0-9]+\.'
    harvard_regex = r'[A-Za-z]+\s\([0-9]+\)\.\s[A-Za-z0-9,:\s]+[A-Za-z]+\.'
    vancouver_regex = r'\[[0-9]+\]\s[A-Za-z0-9,:\s]+\.[\sA-Za-z]+[\s0-9]+[:;][\s0-9]+\.'

    # Count the number of matches for each reference format
    apa_count = len(re.findall(apa_regex, chunk))
    mla_count = len(re.findall(mla_regex, chunk))
    chicago_count = len(re.findall(chicago_regex, chunk))
    harvard_count = len(re.findall(harvard_regex, chunk))
    vancouver_count = len(re.findall(vancouver_regex, chunk))

    # Calculate the total number of references and non-reference text
    total_references = apa_count + mla_count + chicago_count + harvard_count + vancouver_count
    total_text = len(chunk) - sum([apa_count, mla_count, chicago_count, harvard_count, vancouver_count])

    # Check if the majority of the chunk consists of references
    if total_references > total_text:
        return True
    else:
        return False

# def check_references(chunk):
#     # Split the text into lines
#     lines = chunk.split("\n")

#     # Count the number of lines that contain references
#     reference_count = 0
#     for line in lines:
#         if re.match(r'\[[0-9]+\]', line):
#             reference_count += 1

#     # Calculate the ratio of reference lines to total lines
#     ratio = reference_count / len(lines)

#     # Check if the majority of lines contain references
#     if ratio > 0.5:
#         return True
#     else:
#         return False


if __name__ == '__main__':

    chunk = '[28] Romain Paulus, Caiming Xiong, and Richard Socher. A deep reinforced model for abstractive summarization. arXiv preprint arXiv:1705.04304, 2017. [4] Jianpeng Cheng, Li Dong, and Mirella Lapata. Long short-term memory-networks for machine reading. arXiv preprint arXiv:1601.06733, 2016.  [37] Vinyals & Kaiser, Koo, Petrov, Sutskever, and Hinton. Grammar as a foreign language. In Advances in Neural Information Processing Systems, 2015. [24] Minh-Thang Luong, Hieu Pham, and Christopher D Manning. Effective approaches to attention- based neural machine translation. arXiv preprint arXiv:1508.04025, 2015. 5 Training This section describes the training regime for our models.'
    print(check_references(chunk))