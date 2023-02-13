import pikepdf

#Open PDF with pikepdf
pdf = pikepdf.Pdf.open('webpage.pdf')

#Extract metadata from PDF
pdf_info = pdf.docinfo

#Print out the metadata
for key, value in pdf_info.items():
    print(key, ':', value)
