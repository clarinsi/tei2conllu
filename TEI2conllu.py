import conllu
import xml.etree.ElementTree as ET
import argparse


# returns paragraph id
def get_para_id(paragraph):
    return paragraph.attrib["{http://www.w3.org/XML/1998/namespace}id"]


# returns document id
def get_doc_id(doc):
    return doc.attrib["{http://www.w3.org/XML/1998/namespace}id"]


# returns sentence id
def get_sent_id(sentence):
    return sentence.attrib["{http://www.w3.org/XML/1998/namespace}id"]


# returns sentence text
def get_sent_text(sentence):
    sent_text = ""
    for element in sentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}seg":
            for word in element:
                if "join" in word.attrib.keys():
                    sent_text += word.text + ""
                else:
                    sent_text += word.text + " "
        elif element.tag != "{http://www.tei-c.org/ns/1.0}linkGrp" and "join" in element.attrib.keys():
            sent_text += element.text + ""
        elif element.tag != "{http://www.tei-c.org/ns/1.0}linkGrp" and "join" not in element.attrib.keys():
            sent_text += element.text + " "
    sent_text = sent_text.rstrip()
    return sent_text


# used in the writeNoLinks function, splits up a token attribute and returns the upos and feats tags
def split_up_attribute(attribute):
    upos_tag = attribute.split("|")[0][8:]
    feats_in_string = attribute.split("|")[1:]
    feats = {}
    for feature in feats_in_string:
        name, value = feature.split("=")
        feats[name] = value
    return upos_tag, feats


# used in write_elements. Checks if word is punctuation or word and then fills the conllu sentence
# accordingly.
def write_no_links(element, conllu_sentence):
    if element.tag == "{http://www.tei-c.org/ns/1.0}w":

        upos_tag, feats = split_up_attribute(element.attrib["msd"])

        conllu_sentence.append({"id": int(element.attrib["{http://www.w3.org/XML/1998/namespace}id"].split(".")[-1][1:]),
                               "form": element.text, "lemma": element.attrib["lemma"], "upos": upos_tag,
                               "xpos": element.attrib["ana"][4:], "feats": feats, "head": None, "deprel": None,
                               "deps": None, "misc": None})
    elif element.tag == "{http://www.tei-c.org/ns/1.0}pc":

        upos_tag = element.attrib["msd"].split("=")[1]

        conllu_sentence.append({"id": int(element.attrib["{http://www.w3.org/XML/1998/namespace}id"].split(".")[-1][1:]),
                               "form": element.text, "lemma": element.text, "upos": upos_tag,
                               "xpos": element.attrib["ana"][4:], "feats": None, "head": None, "deprel": None,
                               "deps": None, "misc": None})
    if element.tag != "{http://www.tei-c.org/ns/1.0}linkGrp" and "join" in element.attrib.keys():
        conllu_sentence[-1]["misc"] = {"SpaceAfter": "No"}


# takes a sentence from TEI and a sentence from conllu and fills the conllu sentence with all annotations except the
# syntactic links
def write_elements(tei_sentence, conllu_sentence):
    for element in tei_sentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}seg":
            for word in element:
                write_no_links(word, conllu_sentence)
        else:
            write_no_links(element, conllu_sentence)


# takes a sentence from TEI and a sentence from conllu and fills the conllu sentence with UD links
def write_ud_links(tei_sentence, conllu_sentence):
    for element in tei_sentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}linkGrp" and element.attrib["type"] == "UD-SYN":
            for link in element:
                link_name = link.attrib["ana"][7:]
                head, dependent = link.attrib["target"].split(" ")
                if link_name == "root":
                    head = 0
                else:
                    head = int(head.split(".")[-1][1:])
                dependent = int(dependent.split(".")[-1][1:]) - 1
                conllu_sentence[dependent]["head"] = head
                conllu_sentence[dependent]["deprel"] = link_name


# takes a sentence from TEI and a sentence from conllu and fills the conllu sentence with JOS links
def write_jos_links(tei_sentence, conllu_sentence):
    for element in tei_sentence:
        if element.tag == "{http://www.tei-c.org/ns/1.0}linkGrp" and element.attrib["type"] == "JOS-SYN":
            for link in element:
                link_name = link.attrib["ana"][8:]
                head, dependent = link.attrib["target"].split(" ")
                if link_name == "modra":
                    head = 0
                else:
                    head = int(head.split(".")[-1][1:])
                dependent = int(dependent.split(".")[-1][1:]) - 1
                conllu_sentence[dependent]["head"] = head
                conllu_sentence[dependent]["deprel"] = link_name


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

#check if TEI file has the right sequence of elements
if root[0].tag == "{http://www.tei-c.org/ns/1.0}bibl" and root[1].tag == "{http://www.tei-c.org/ns/1.0}p":
    print("Sequence of elements in file is OK")
else:
    raise Exception("The sequence of elements in the TEI XML is not supported")

# prepare list of conllu sentences
ConlluSentences = []

# go through all the TEI sentences and write all the data from each sentence to a new conllu TokenList object. At the
# end, append the TokenList to the list of conllu sentences
doc_id = get_doc_id(root)
for ele in root:
    if ele.tag == "{http://www.tei-c.org/ns/1.0}p":
        para_id = get_para_id(ele)
        for tei_sent in ele:
            sent_to_write = conllu.TokenList()

            if tei_sent == root[1][0]:
                sent_to_write.metadata.update({"newdoc id": doc_id})

            if tei_sent == ele[0]:
                sent_to_write.metadata.update({"newpar id": para_id})

            sent_id = get_sent_id(tei_sent)
            sent_to_write.metadata.update({"sent_id": sent_id})

            tei_sent_text = get_sent_text(tei_sent)
            sent_to_write.metadata.update({"text": tei_sent_text})

            write_elements(tei_sent, sent_to_write)

            if args.syn == "UD":
                write_ud_links(tei_sent, sent_to_write)
            else:
                write_jos_links(tei_sent, sent_to_write)

            ConlluSentences.append(sent_to_write)

# go through the conllu sentence list and write to a .conllu file
with open(f"{args.file[:-3]}conllu", "w", encoding="UTF-8") as write_file:
    for sent_in_conllu in ConlluSentences:
        write_file.write(sent_in_conllu.serialize())
