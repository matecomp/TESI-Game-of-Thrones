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
			path = directory+dirname
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
	text = preprocessing(text)
	return text

def preprocessing(text):
	text = text.decode("utf8")
	#Remove as multiplas quebras de linha para extrair os dados iniciais
	text = re.sub(r"\n\n+", ".\n", text)
	#Remove caracteres indesejados
	text = re.sub(u'[^a-zA-Z0-9.,\n \']', ' ', text)
	#Separar , da palavra
	text = re.sub(",", " , ", text)
	#Remove espacos consecutivos
	text = re.sub(r"  +", " ", text)
	#Adiciona . em cada quebra de linha para ajudar a extracao de sentencas
	text = re.sub(r"\.* *\n+", ".\n", text)
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
	places = ["into","between","in","from"]
	humans = ['king','lord commander','commander','lord','maester','lady','son','bastard'
				'master','prince','princess','queen','sir','ser','regent','old']
	for sent in tagged_sentences:
		aux = []
		for word,tag in sent:
			aux_word = word.lower()
			if aux_word == "of":
				tag = "OF"
			elif aux_word == "the":
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
	  ORGANIZATION:
	  	{<NP>+<OF><NP>+}
	  HOUSES:
	  	{<HOUSE><OF>?<NP>+}		# NP is better than anyway tag in this case

	  """
	# PEOPLE:
	#   	{<STATUS><NP>+}
	#   LOCATION:
	#   	{<LOC><DA><NP\+|.*>}
	cp = nltk.RegexpParser(grammar)
	NE = set()
	
	for sent in tagged_sentences:
		tree = cp.parse(sent)
		for subtree in tree.subtrees():
			if subtree.label() != "S":
				entity = Subtree2Text(subtree)
				lower_entity = entity.lower() + ": "
				class_entity = subtree.label() + ": "
				text = entity #class_entity + lower_entity + entity
				if text not in NE:
					NE.add(text)
	return NE

def extractNE(data_json):
	episode_text = Json2Content(data_json)
	tagged_sentences = TaggerText(episode_text)
	NE_aux = Chunker(tagged_sentences)
	NE = set()
	#Remove entidades que apareceram uma unica vez
	for n in NE_aux:
		freq_n = episode_text.count(n)
		if freq_n > 1 or "house " in n.lower() or "game " in n.lower():
			NE.add(n)

	episode_text = episode_text.lower()

	return NE, episode_text

def allNER():
	NE = set()
	episode_text = ""
	for season in seasons:
		for episode in season:
			print "Processing: ", episode
			data_json = openJson(episode)
			tempNE, tempText = extractNE(data_json)
			NE.update(tempNE)
			episode_text += tempText + '\n'
	return NE, episode_text

def markNER(text):
	callback = lambda pat: pat.group(0).upper()
	uNE = sorted(NE, reverse=True)
	stopwords = nltk.corpus.stopwords.words("english")
	stopwords.append(["first","news","three"])
	for n in uNE:
		n = n.lower()
		n = n.split(" ")
		for i in n:
			if len(i) > 2 and i not in stopwords:
				log_str = "( +|\.|\n)"+i+"( +|\.|\n|s|'s|')"
				text = re.sub(log_str, callback, text, flags=re.IGNORECASE)

	callback = lambda pat: pat.group(0).lower()
	text = re.sub(r"([A-Z])+([a-z])", callback, text)
	text = re.sub(r"([a-z])([A-Z])+", callback, text)
	text = re.sub(r"'S", " 'S", text)
	text = re.sub(r"'", " '", text)
	return text

def pre_NCE_Classifier(marked_text):
	valid_text = ""
	for line in marked_text.split('\n'):
		if len(line) > 60:
			valid_text += "BEGIN BEGIN " + line + " END END\n"

	# valid_text = re.sub(r"'s", "", valid_text)
	valid_text = re.sub(r"\. ", " END END BEGIN BEGIN ", valid_text)
	valid_text = re.sub(r"BEGIN BEGIN END END", "", valid_text)
	valid_text = re.sub(u'[^a-zA-Z0-9.\n \']', '', valid_text)
	return valid_text


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


if __name__ == '__main__':
	#Pasta de onde os textos serao obtidos
	mypath = "../episodesJSON"
	#Lista com o endereco de cada arquivo txt
	seasons = list_files(mypath)
	#Lista ordenada sem repeticao das endidades
	# NE, episode_text = allNER()
	NE = loadCSV("Naive-NER.csv")

	NE = removeSubstring(NE)
	NE = sorted(NE)

	#Extrai o corpus de GoT
	f = open("../DATASET/episode_text.txt", "rb")
	episode_text = f.read()
	f.close()

	#Marca as entidades no corpus de GoT
	marked_text = markNER(episode_text)

	#Preprocessamento para o tensorflow
	valid_text = pre_NCE_Classifier(marked_text)

	f = open("../DATASET/dataset.txt", "wb")
	f.write(marked_text)
	f.close()

	f = open("../DATASET/dataset_nce.txt", "wb")
	f.write(valid_text)
	f.close()

	print len(NE)
	saveCSV('Naive-NER.csv', NE)
	print "Done"
			
			
