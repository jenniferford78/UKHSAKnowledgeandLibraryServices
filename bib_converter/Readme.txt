Usage:
Run the bib_convert_run.py file using python 3 (py bib_convert_run.py, with file associations double-click the file)
Prompts to browse for input file in local file system
Prompts for output type (list of databases presented)
Prompts to browse for output file (will overwrite if file exists)
Format of output file is line-by-line translation followed by line-by-line of warnings matching the line

Supports:
Stripping line numbers and record counts
Field-level query translation
Adjacency operators

Current implementation:
(Limitations can be overcome with more development time - seeking to understand priorities)
Only maps from Ovid to other databases
Does not support multiple field conditions
Does not support search term between databases

Known issues:
Does not current support Ovid 'adj' operator
PubMed adjacency operators have less control than in other databases (as they are field-query-level)