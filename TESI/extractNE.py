# -*- coding: utf-8 -*-
import nltk
import re
import sys
import csv as csv
reload(sys)
sys.setdefaultencoding('utf-8')

#Para este trabalho utilizei o perceptronTagger...
# import inspect
# def pos_tag(tokens, tagset=None):
# 	tagger = PerceptronTagger()
# 	return _pos_tag(tokens, tagset, tagger)
# from nltk import pos_tag


#Cria uma lista com o endereco de todos os arquivos txt dentro de alguma pasta
from os import listdir
from os import walk
from os.path import isfile, join
def list_files(directory):
	files = []
	for (dirpath, dirnames, filenames) in walk(directory):
		for dirname in dirnames:
			path = mypath+'/'+dirname
			files.append([path+'/'+file for file in listdir(path) if isfile(join(path, file))])
	return files

#Metodos para extrair dado do arquivo JSON do Guilherme
import json
def openJson(archive):
	with open(archive) as data_file:
		data = json.load(data_file)
	return data

def Json2Content(data_json):
	paragraph = data_json['summary']
	text = data_json['info'] + '\n'
	text += data_json['plot'] + '\n'
	for p in paragraph:
		text += p['content'] + '\n'
	return text


#Classifica gramaticalmente cada palavra do texto com uma tag
def TaggerText(text):
	#Extrair sentencas
	tokenized_sentences = nltk.sent_tokenize(text)
	#Extrair palavras
	tokenized_words = [nltk.word_tokenize(sent) for sent in tokenized_sentences]
	#Tagger lista de lista de words
	tagged_sentences = [nltk.pos_tag(wordlist) for wordlist in tokenized_words]
	#Renomear tags
	temp = []
	places = ["at","near","on","along","into","inside",
				"in","from"]
	humans = ['king','lord commander','lord','maester',
				'master','prince','princess','queen','sir']
	for sent in tagged_sentences:
		aux = []
		for word,tag in sent:
			aux_word = word.lower()
			if aux_word == "of":
				tag = "OF"
			if aux_word == "the":
				tag = "DA"
			elif word == "House":
				tag = "HOUSE"
			elif aux_word in places:
				tag = "LOC"
			elif aux_word in humans:
				tag = "STATUS"
			aux.append((word,tag))
		temp.append(aux)

	tagged_sentences = temp
	return tagged_sentences

#Remove os caracteres especiais adicionado no objeto subtree do NLTK
def Subtree2Text(subtree):
	text = str(subtree)
	text = re.sub(r"\([A-Z]+ *| *[A-Z]+\)|/[A-Z]*\)?|\)","", text)
	text = re.sub(r" *\n+"," ", text)
	text = re.sub(r"  +"," ", text)
	text = re.sub(r"^\s+","", text)
	text = re.sub(u"[^a-zA-Z0-9 \']", '', text)
	return text

#Remove as entidades que estao contidas em outra entidade
def removeSubstring(string_list):
	words = set()
	for s in string_list:
		if not any([s+' ' in word or ' '+s in word or (' ' in s and s in word and s != word) or s in words for word in string_list]):
			words.add(s)
	return words


def Chunker(tagged_sentences):

	grammar = r"""
	  NP:
	    {<DT|PRP\$>?<JJ>*<NNP|NNPS>+}   # chunk determiner/possessive, adjectives and noun
	    }<VBD|IN>+{      # Chink sequences of VBD and IN
	    }<POS>{
	  ORGANIZATION:
	  	{<NP><OF><NP>}
	  HOUSES:
	  	{<HOUSE><OF>?<NP>}
	  PEOPLE:
	  	{<STATUS>?<NP>+}
	  NPA:
	  	{<NP><POS>}
	  LOCATION:
	  	{<LOC><DA>?<NPA>}
	  """
	cp = nltk.RegexpParser(grammar)
	NE = set()
	
	for sent in tagged_sentences:
		tree = cp.parse(sent)
		for subtree in tree.subtrees():
			if subtree.label() != "S":
				entity = Subtree2Text(subtree)
				lower_entity = entity.lower() + ": "
				class_entity = subtree.label() + ": "
				if text not in NE:
					NE.add(class_entity + lower_entity + entity)
	return NE

def extractNE(data_json):
	episode_text = Json2Content(data_json)
	tagged_sentences = TaggerText(episode_text)
	NE_aux = Chunker(tagged_sentences)
	NE = set()
	#Remove entidades que apareceram uma unica vez
	for n in NE_aux:
		n = n.split(': ')
		if episode_text.count(n[2]) > 1:
			NE.add(n[0] +" : "+ n[1])


	return NE, episode_text


def saveNE(name, values):
	#Etapas para criar o arquivo csv e escrever todo conteudo em N neste arquivo
	target_file = open(name, "wb")
	open_file_object = csv.writer(target_file)
	open_file_object.writerow(["NER"])
	for item in values:
		open_file_object.writerow([item,])
	target_file.close()

if __name__ == '__main__':
	#Pasta de onde os textos serao obtidos
	mypath = "episodesJSON"
	#Lista com o endereco de cada arquivo txt
	seasons = list_files(mypath)
	#Lista ordenada sem repeticao das endidades
	NE = set()
	text = ""
	for season in seasons:
		for episode in season:
			print "Processing: ", episode
			data_json = openJson(episode)
			tempNE, tempText = extractNE(data_json)
			NE.update(tempNE)
			text += tempText + '\n'

	# ValidText = ""
	# for line in text.split('\n'):
	# 	if len(line) > 60:
	# 		ValidText += "BEGIN BEGIN " + line.lower() + " END END\n"

	# ValidText = re.sub(r"'s", "", ValidText)
	# ValidText = re.sub(r"\. ", " END END BEGIN BEGIN ", ValidText)
	# ValidText = re.sub(r"BEGIN BEGIN END END", "", ValidText)
	# ValidText = re.sub(u'[^a-zA-Z0-9.\n ]', '', ValidText)
	# f = open("base_de_dados.txt", "wb")
	# f.write(ValidText)
	# f.close()

	#Remove entidades que estão contidas em outras
	# NE = removeSubstring(NE)
	NE = sorted(NE)


	print len(NE)
	saveNE('NER.csv', NE)
	print "Done"
			
			
