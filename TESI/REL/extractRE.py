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
	open_file_object.writerow(["RELATION;EPISODE;LOCATION"])
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
	text = ""
	flag = False
	for word in subtree.flatten()[:]:
		if word[1] == 'OPENS': flag = True
		if word[1] == 'LOCKS': flag = False
		if word[0] != ']' and word[0] != '[' and (flag or "VB" in word[1]):
			text += word[0] + " "
	text = text[0:-1]
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
			if aux_word == "[":
				tag = "OPENS"
			if aux_word == "]":
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
				relation = Subtree2Text(subtree)
				print relation
				if relation not in RE:
					RE.add(relation)
	return RE



import xml.etree.ElementTree as ET
def extractRE(path, NE):
	f = open(path)
	raw_text = f.read()
	f.close()
	episodes = ET.fromstring(raw_text)
	RE = set()
	for episode in episodes:
		episode_name = " ; "+episode.attrib['id']
		for chapter in episode:
			if chapter.tag == 'location':
				chapter_name = " ; "+chapter.attrib['id']
			tagged_sentences = TaggerText(chapter.text)
			tempRE = Chunker(tagged_sentences)
			labels = re.sub(",", "", episode_name + chapter_name)
			RE.update([(r + labels).encode('utf-8') for r in tempRE])
	return RE



if __name__ == '__main__':

	path = "../DATASET/normalizeNE.txt"

	NE = loadCSV("../NER/ENTITIES/Naive-NER.csv")
	print len(NE)

	RE = extractRE(path, NE)
	# for relation in RE:
		# print relation , '\n\n'
	print len(RE)
	saveCSV('RELATIONS/Naive-REL.csv', RE)


