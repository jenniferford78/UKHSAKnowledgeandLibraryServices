# Takes a folder and a list of terms
# Outputs a csv in the folder with 
# Terms, files, first 10 pages with term, first 3 contexts of term
# Requires pdfplumber (install with pip install pdfplumber)
# Known limitation - some effort is made to extract terms which overlap between pages but there may be bugs


# Terms are regexes
# Useful bits:
# literals (e.g. corona)
# wildcards - . is any character, \w is any letter, \W any non-letter, \d any digit, \s any whitespace character, [asdf] is any of a, s, d, f
# These can be modified by ? (0 or 1), + (1+), * (0+), {3, 5} (3-5)
# So e.g. tumou?r will match tumor or tumour, 
# prostate\s(\w+\s+){,3}cancer will match 'prostate cancer' or 'prostate or lung cancer' but not 'prostate, or lung cancer' (the comma isn't whitespace)
# prostate\W+(\w+\W+){,3}cancer will match 'prostate, bowel or lung cancer' but not 'prostate, bowel, brain or lung cancer' (the search term required at most 3 intervening words)
# Documentation at https://docs.python.org/3/library/re.html#
# https://regex101.com/ is a handy tester


import pandas as pd
import pdfplumber
import os
import re
from itertools import accumulate

spacing_around_context = 50 #characters
terms_filename = 'terms.txt'
search_flags = re.IGNORECASE

# term, file, pages found
# term, file, index of context, page, context

def extract_pages(working_folder, filename):
    with pdfplumber.open(os.path.join(working_folder, filename)) as pdf:
        extracted_text = [page.extract_text() for page in pdf.pages]
    return extracted_text

def clean_page(page_string):
    # Appropriate steps to aid in text matching, e.g.
    # Replacing line breaks with whitespace
    cleaned_string = re.sub(r'\n', ' ', page_string, count = 0)
    return cleaned_string

def process_file(filename):
    extracted_text = extract_pages(working_folder, filename)
    cleaned_pages = [clean_page(page) for page in extracted_text]
    page_sizes = [len(page) + 1 for page in cleaned_pages]
    cumulative_page_sizes = list(accumulate(page_sizes))
    page_ranges = list(enumerate(zip([0]+cumulative_page_sizes[:-1], cumulative_page_sizes)))
    concatenated_pages = ' '.join(cleaned_pages)

    def get_page(position):
        page = min([page_range[0] for page_range in page_ranges if position >= page_range[1][0] and position < page_range[1][1]])
        return page

    def get_context(span):
        start = max(span[0] - spacing_around_context, 0)
        end = min(span[1] + spacing_around_context, cumulative_page_sizes[-1]-1)
        return concatenated_pages[start:end]

    def search_for_term(term):
        matches = list(re.finditer(term, concatenated_pages, flags = search_flags))
        pages = [get_page(match.start(0)) for match in matches]
        contexts = [get_context(match.span(0)) for match in matches]
        return pd.DataFrame(data = {
            'filename': [filename for match in matches],
            'term': [term for match in matches],
            'matched_term': [match.group(0) for match in matches],
            'page': pages,
            'context': contexts
        })

    result_dataframes = [search_for_term(term) for term in terms]
    file_processed_dataframe = pd.concat(result_dataframes)
    return file_processed_dataframe

# Prompts for a folder and goes from there

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askdirectory, asksaveasfile
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

working_folder = askdirectory(mustexist=True)

with open(os.path.join(working_folder, terms_filename), 'r') as terms_file:
    terms = terms_file.read().split('\n')

files = list(os.scandir(working_folder))
pdf_filenames = [entry.name for entry in files if entry.is_file() and entry.name.endswith('.pdf')]
processed_file_dataframes = [process_file(filename) for filename in pdf_filenames]
full_dataframe = pd.concat(processed_file_dataframes)

output_file = asksaveasfile(defaultextension=".csv", filetypes=(("comma separated values", "*.csv"),("All Files", "*.*") ))
full_dataframe.to_csv(output_file)
output_file.close()