# -*- coding: utf-8 -*-
import collections
import nltk
import csv
import re
import nltk

def saveCSV(name, values):
	#Etapas para criar o arquivo csv e escrever todo conteudo em N neste arquivo
	target_file = open(name, "wb")
	open_file_object = csv.writer(target_file)
	open_file_object.writerow(["NER"])
	for item in values:
		open_file_object.writerow([item,])
	target_file.close()

def loadCSV(archive):
	group = set()
	with open(archive, 'rb') as csvfile:
		words = csv.reader(csvfile)
		for word in words:
			if word[0] != "NER":
				group.update(word)
	return group

#Remove os caracteres especiais adicionado no objeto subtree do NLTK
def Subtree2Text(subtree):
	text = str(subtree)
	text = re.sub(r"\([A-Z]+ *| *[A-Z]+\)|/[A-Z]*\)?|\)","", text)
	text = re.sub(r" *\n+"," ", text)
	text = re.sub(r"  +"," ", text)
	text = re.sub(r"^\s+","", text)
	text = re.sub(u"[^a-zA-Z0-9 \']", '', text)
	return text

#Classifica gramaticalmente cada palavra do texto com uma tag
def TaggerText(text):
	#Extrair sentencas
	tokenized_sentences = nltk.sent_tokenize(text)
	#Extrair palavras
	tokenized_words = [nltk.word_tokenize(sent) for sent in tokenized_sentences]
	#Tagger lista de lista de words
	tagged_sentences = [nltk.pos_tag(wordlist) for wordlist in tokenized_words]
	
	temp = list()
	for sent in tagged_sentences:
		aux = []
		for word,tag in sent:
			aux_word = word.lower()
			if aux_word == "<":
				tag = "OPENS"
			if aux_word == ">":
				tag = "LOCKS"
			aux.append((word,tag))
		temp.append(aux)

	tagged_sentences = temp
	return tagged_sentences

def Chunker(tagged_sentences):

	grammar = r"""
	  ENT:
	  	{<OPENS><..?.?.?>+<LOCKS>}
	  REL:
	  	{<ENT><.+>?<.+>?<VB.*><.+>?<.+>?<ENT>}
	  """

	cp = nltk.RegexpParser(grammar)
	RE = set()
	
	for sent in tagged_sentences:
		tree = cp.parse(sent)
		for subtree in tree.subtrees():
			if subtree.label() == "REL":
				entity = Subtree2Text(subtree)
				text = entity
				if text not in RE:
					RE.add(text)
	return RE



def extractRE(text, NE):
	tagged_sentences = TaggerText(text)
	RE = Chunker(tagged_sentences)
	return RE

if __name__ == '__main__':

	f = open("../DATASET/normalizeNE.txt")
	normalize_text = f.read()
	f.close()

	NE = loadCSV("../NER/ENTITIES/Naive-NER.csv")

	print len(NE)
	RE = extractRE(normalize_text, NE)
	# for relation in RE:
		# print relation , '\n\n'
	print len(RE)
	# saveCSV('RELATIONS/Naive-REL.csv', NE)


