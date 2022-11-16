import conllu
import xml.etree.ElementTree as ET
import argparse

# returns sentence id
def getSentID(sentence):
    return sentence.attrib["{http://www.w3.org/XML/1998/namespace}id"]

# returns sentence text
def getSentText(sentence):
    SentText = ""
    for element in sentence:
        if element.tag != "{http://www.tei-c.org/ns/1.0}linkGrp" and "join" in element.attrib.keys():
            SentText += element.text + ""
        elif element.tag != "{http://www.tei-c.org/ns/1.0}linkGrp" and not "join" in element.attrib.keys():
            SentText += element.text + " "
    SentText = SentText.rstrip()
    return SentText

# used in the writeElementsNoLinks function, splits up a token attribute and returns the upos and feats tags
def SplitUpAttribute(attribute):
    UposTag = attribute.split("|")[0][8:]
    FeatsInString = attribute.split("|")[1:]
    Feats = {}
    for feature in FeatsInString:
        name, value = feature.split("=")
        Feats[name] = value
    return UposTag, Feats

# takes a sentence from TEI and a sentence from conllu and fills the conllu sentence with all annotations except the
# syntactic links
def writeElementsNoLinks(TEISentence, ConlluSentence):
    for element in TEISentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}w":

            UposTag, Feats = SplitUpAttribute(element.attrib["msd"])

            ConlluSentence.append({"id": int(element.attrib["{http://www.w3.org/XML/1998/namespace}id"].split(".")[-1]),
                                   "form": element.text, "lemma": element.attrib["lemma"], "upos": UposTag,
                                   "xpos": element.attrib["ana"][4:], "feats": Feats, "head": None, "deprel": None,
                                   "deps": None, "misc": None})
        elif element.tag == "{http://www.tei-c.org/ns/1.0}pc":

            UposTag = element.attrib["msd"].split("=")[1]

            ConlluSentence.append({"id": int(element.attrib["{http://www.w3.org/XML/1998/namespace}id"].split(".")[-1]),
                                   "form": element.text, "lemma": element.text, "upos": UposTag,
                                   "xpos": element.attrib["ana"][4:], "feats": None, "head": None, "deprel": None,
                                   "deps": None, "misc": None})
        if element.tag != "{http://www.tei-c.org/ns/1.0}linkGrp" and "join" in element.attrib.keys():
            ConlluSentence[-1]["misc"] = {"SpaceAfter": "No"}

# takes a sentence from TEI and a sentence from conllu and fills the conllu sentence with UD links
def writeUDSynLinks(TEIsentence, ConlluSentence):
    for element in TEIsentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}linkGrp" and element.attrib["type"] == "UD-SYN":
            for link in element:
                LinkName = link.attrib["ana"][7:]
                head, dependent = link.attrib["target"].split(" ")
                if LinkName == "root":
                    head = 0
                else:
                    head = int(head.split(".")[-1])
                dependent = int(dependent.split(".")[-1]) - 1
                ConlluSentence[dependent]["head"] = head
                ConlluSentence[dependent]["deprel"] = LinkName

# takes a sentence from TEI and a sentence from conllu and fills the conllu sentence with JOS links
def writeJOSSynLinks(TEIsentence, ConlluSentence):
    for element in TEIsentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}linkGrp" and element.attrib["type"] == "JOS-SYN":
            for link in element:
                LinkName = link.attrib["ana"][8:]
                head, dependent = link.attrib["target"].split(" ")
                if LinkName == "modra":
                    head = 0
                else:
                    head = int(head.split(".")[-1])
                dependent = int(dependent.split(".")[-1]) - 1
                ConlluSentence[dependent]["head"] = head
                ConlluSentence[dependent]["deprel"] = LinkName

# main part of the script
# argparse
argparser = argparse.ArgumentParser(description="Convert TEI XML file to .conllu file.")
argparser.add_argument("file", type=str, help="Name of the TEI XML file to be converted.")
argparser.add_argument("--syn-type", dest="syn", type=str, choices=["UD", "JOS"], default="UD",
                       help="Syntactic relation type to be included (UD or JOS). Defaults to UD.")
args = argparser.parse_args()

# import TEI XML data with ElementTree
tree = ET.parse(args.file)
root = tree.getroot()

# prepare list of conllu sentences
ConlluSentences = []

# go through all the TEI sentences and write all the data of each sentence to a new conllu TokenList object. At the end,
# append the TokenList to the list of conllu sentences
for body in root[1]:
    for paragraph in body:
        for sentence in paragraph:
            SentToWrite = conllu.TokenList()

            SentID = getSentID(sentence)
            SentToWrite.metadata.update({"sent_id": SentID})

            SentText = getSentText(sentence)
            SentToWrite.metadata.update({"text": SentText})

            writeElementsNoLinks(sentence, SentToWrite)

            if args.syn == "UD":
                writeUDSynLinks(sentence, SentToWrite)
            else:
                writeJOSSynLinks(sentence, SentToWrite)

            ConlluSentences.append(SentToWrite)

# go through the conllu sentence list and write to a .conllu file
with open(f"{args.file[:-3]}conllu", "w", encoding="UTF-8") as write_file:
    for SentInConllu in ConlluSentences:
        write_file.write(SentInConllu.serialize())