|Model field|Type|Dublin Core source|Notes / what gets lost|
|-----------|----|------------------|----------------------|
identifier|str|< identifier>|In the header (same as the second dc:identifier)|
title|str|<dc:title>||
creators|list[str]|<dc:creator>|Last name first then a comma then the first name|
publication_year|int  None|<dc:date>|Pure date, not a timestamp. Format YYYY-MM-DD|
subjects|list[str]|<dc:subject>||
description|str  None|<dc:description>|Unescape HTML then removing HTML tag|
doi|str  None|<dc:identifier>|dc:identifier is the DOI of this version while dc:relation is the concept DOI, which points to all versions.|
source|str|Set by the harvester not from the XML|
language|str  None|<dc:language>||
not mapped||<dc:rights>/<dc:publisher>/<dc:type>/<dc:relation>||