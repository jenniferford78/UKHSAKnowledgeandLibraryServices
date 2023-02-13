from pypdf import PdfReader
import datetime
import sys
for file in sys.argv:
    print(file)
    with open (file, "rb") as f:
        reader = PdfReader(f)
        number_of_pages = len(reader.pages)
        page = reader.pages[0]
        meta = reader.metadata
        text = page.extract_text()# Write your code here :-)
        line = text.split("\n")
        filename = meta.author + meta.creation_date.strftime('%Y')
        print(filename)

#print(meta.author)
#print(meta.creation_date)
#print(meta.title)
#print(meta.creation_date.year)

