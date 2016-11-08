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
	episode_text = ""
	for season in seasons:
		for episode in season:
			print "Processing: ", episode
			data_json = openJson(episode)
			tempNE, tempText = extractNE(data_json)
			NE.update(tempNE)
			episode_text += tempText + '\n'


	callback = lambda pat: pat.group(0).upper()
	uNE = sorted(NE, reverse=True)
	stopwords = nltk.corpus.stopwords.words("english")
	stopwords.append("first")
	for n in uNE:
		n = n.lower()
		n = n.split(" ")
		for i in n:
			if len(i) > 2 and i not in stopwords:
				log_str = "( +|\.|\n)"+i+"( +|\.|\n|s|'s|')"
				episode_text = re.sub(log_str, callback, episode_text, flags=re.IGNORECASE)

	callback = lambda pat: pat.group(0).lower()
	episode_text = re.sub(r"([A-Z])+([a-z])", callback, episode_text)
	episode_text = re.sub(r"([a-z])([A-Z])+", callback, episode_text)
	
	c1 = lambda pat: pat.group(1)+"_"+pat.group(2)
	episode_text = re.sub(r"([A-Z]) ([A-Z])", c1, episode_text)
	episode_text = re.sub(r"'S_", "'S ", episode_text)

	






	# ValidText = ""
	# for line in text.split('\n'):
	# 	if len(line) > 60:
	# 		ValidText += "BEGIN BEGIN " + line + " END END\n"

	# # ValidText = re.sub(r"'s", "", ValidText)
	# ValidText = re.sub(r"\. ", " END END BEGIN BEGIN ", ValidText)
	# ValidText = re.sub(r"BEGIN BEGIN END END", "", ValidText)
	# ValidText = re.sub(u'[^a-zA-Z0-9._[]\n \']', '', ValidText)
	
	NE = removeSubstring(NE)
	NE = sorted(NE)

	f = open("base_de_dados.txt", "wb")
	f.write(episode_text)
	f.close()

	print len(NE)
	saveNE('Naive-NER.csv', NE)
	print "Done"
			
			
