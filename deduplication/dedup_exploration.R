install.packages('revtools') #potentially interesting tool for loading RIS files

library(tidyverse)
library(revtools)
bibliography = read_bibliography('C:/Users/Cong.Chen/Downloads/202212STECReviewALL.txt')
sort(colnames(bibliography))
# [1] "a2"                "abstract"          "address"           "AO"                "author"            "c1"                "c2"               
# [8] "c3"                "c4"                "doi"               "ID"                "institution"       "issn"              "issue"            
# [15] "journal"           "journal_secondary" "keywords"          "l2"                "label"             "language"          "m1"               
# [22] "m2"                "pages"             "publisher"         "title"             "type"              "url"               "volume"           
# [29] "XT"                "year"     

# look at author, year, title, journal

bibliography %>% count(author, year, title, journal) %>% count(n)
bibliography %>% count(title) %>% count(n)

