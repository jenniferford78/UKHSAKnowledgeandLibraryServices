Usage:
Install the pdfplumber Python package (https://github.com/jsvine/pdfplumber) by running 'pip install pdfplumber' or 'py -m pip install pdfplumber' at the command line
Install the pandas Python package the same way ('py -m pip install pandas')
You may also require the tqdm package ('py -m pip install tqdm')
Put a terms.txt file in the target folder with the desired search terms
Run the search_in_files.py file 
Prompts to browse for target folder
Prompts for how many results per file/search term combination to return (default is 0 which means all results)
Prompts to browse for output file (CSV file, will overwrite if file exists)
Format of output file is a table with columns for the filename, the term, the specific instance of the term that was matched, the occurence index of the term in the document, the page on which it was found and some context for the term found
To for instance restrict to the first 3 or 1 instances of the term in each document filter on the 'occurence' column in Excel
