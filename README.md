# tei2conllu

Python script for converting TEI XML to CoNLL-U. This is still a bare-bones version, so it currently works only on a very specific type of TEI file. The goal is to eventually have a conversion script that works with the type of format used by the upcoming SUK corpus. 

The script defaults to writing UD dependency links, but the "--syn-type JOS" option can be added to make it write JOS dependency links.
