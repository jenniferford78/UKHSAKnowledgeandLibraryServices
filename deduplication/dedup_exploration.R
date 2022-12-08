install.packages('revtools') #potentially interesting tool for loading RIS files

library(tidyverse)
library(revtools)
bibliography = read_bibliography('C:/Users/Cong.Chen/Downloads/202212STECReviewALL.txt') #Final unique article count is about 8.3K
# Loading performance is very poor - need to use a different tool to process large imports
# This import is also picking up inappropriate fields (e.g. DNA which was part of a keyword)
sort(colnames(bibliography))
# [1] "a2"                "abstract"          "address"           "AO"                "author"            "c1"                "c2"               
# [8] "c3"                "c4"                "doi"               "ID"                "institution"       "issn"              "issue"            
# [15] "journal"           "journal_secondary" "keywords"          "l2"                "label"             "language"          "m1"               
# [22] "m2"                "pages"             "publisher"         "title"             "type"              "url"               "volume"           
# [29] "XT"                "year"     

# look at author, year, title, journal
bibliography$id = 1:nrow(bibliography)
bibliography %>% count(author, year, title, journal) %>% count(n)
bibliography %>% count(title) %>% count(n)

bibliography %>% count(title, journal, year) %>% count(n)
bibliography %>% group_by(title) %>% filter(n_distinct(journal) > 1) %>% arrange(title) %>% View

remove_by_group = function(df, ...){
  # Does not handle missing values appropriately
  df %>% group_by(...) %>%
    mutate(duplicate = row_number()) %>%
    filter(duplicate == 1) %>%
    select(-duplicate) %>%
    ungroup()
}

process_authors = function(authors_entry){
  
}

# Leeds method developed in Endnote
# 1. author + year + title + journal
# 2. author + year + title + pages
# Note pages often can be weird e.g. 203 - 5 = 203-205 or missing in which case the deduplication should not apply
# 3. title + journal + pages
# 4. title + year + pages
# 5. title + pages
# 6. author + year + journal + pages
# 7. author + year + title
# 8. author + year + journal
# 9. author + year #by this point it's pretty hairy
# 10. year + title

# epireviewer tool

cleaned_bib = bibliography %>% 
  transmute(id, 
            title1 = tolower(title),
            journal1 = tolower(journal),
            year,
            author1 = tolower(author),
            pages)
cleaned_bib %>% remove_by_group(title1, journal1, year, author1) -> cleaned_bib_1
cleaned_bib_1 %>% remove_by_group(author1, year, title1, pages) -> cleaned_bib_2
cleaned_bib_2 %>% remove_by_group(title1, journal1, pages) -> cleaned_bib_3
cleaned_bib_3 %>% remove_by_group(year, title1, pages) -> cleaned_bib_4
cleaned_bib_4 %>% remove_by_group(title1, pages) -> cleaned_bib_5
cleaned_bib_5 %>% remove_by_group(author1, year, journal1, pages) -> cleaned_bib_6
cleaned_bib_6 %>% remove_by_group(author1, year, title1) -> cleaned_bib_7
cleaned_bib_7 %>% remove_by_group(author1, year, journal1) -> cleaned_bib_8
