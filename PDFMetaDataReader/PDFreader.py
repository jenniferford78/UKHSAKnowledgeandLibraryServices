from pypdf import PdfReader

reader = PdfReader(r"C:\Users\jenni\OneDrive\Desktop\s13643-018-0784-8.pdf")
number_of_pages = len(reader.pages)
page = reader.pages[0]
meta = reader.metadata
text = page.extract_text()# Write your code here :-)
line = text.split("\n")
print(line[0:5])
print(meta.author)
print(meta.creation_date)
print(meta.subject)
