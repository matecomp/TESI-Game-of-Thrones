# -*- coding: utf-8 -*-
import nltk
import re
import collections
import numpy as np

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

def build_dataset(words):
	count = []
	count.extend(collections.Counter(words).most_common())
	dictionary = dict()
	newcount = list()
	for word, freq in count:
		if freq > 1:
			dictionary[word] = len(dictionary)
			newcount.append([word,freq])
	count = newcount

	data = list()

	for word in words:
		if word is dictionary:
			index = dictionary[word]
			data.append(index)
	reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
	return data, count, dictionary, reverse_dictionary

def removeStopwords(word_text, language=None):
	words = []
	NE = set()
	if language == None:
		stopwords = []
	else:
		stopwords = nltk.corpus.stopwords.words(language)

	words = [w for w in word_text if w not in stopwords]

	return words

#Metodos para extrair dado do arquivo JSON do Guilherme
import json
def openJson(archive):
	with open(archive) as data_file:
		data = json.load(data_file)
	return data

def preprocessing(text):
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

def Json2Content(data_json):
	paragraph = data_json['summary']
	text = data_json['info'] + '\n'
	text += data_json['plot'] + '\n'
	for p in paragraph:
		text += p['content'] + '\n'
	text = preprocessing(text)
	return text

def word2freq(content):
	words = nltk.word_tokenize(content)
	words = removeStopwords(words)
	data, count, dictionary, reverse_dictionary = build_dataset(words)
	return count, dictionary, reverse_dictionary

def build_tf(path, directory):
	#Extrai o corpus de GoT
	f = open(path, "rb")
	episode_text = f.read()
	f.close()


	#Lista com o endereco de cada arquivo txt
	_, dictionary, reverse_dictionary = word2freq(episode_text)

	episodes = list()

	m = len(dictionary)
	matrix = np.zeros([0,m])
	
	seasons = list_files(directory)
	for season in seasons:
		for episode in season:
			print "Processing: ", episode
			episodes.append(episode)
			
			data_json = openJson(episode)
			content = Json2Content(data_json)
			count, _, _  = word2freq(content.lower())
			vector = np.zeros([1,m])
			for word, freq in count:
				col = dictionary[word]
				vector[0,col] = freq
			matrix = np.vstack([matrix,vector])
	print len(episodes),len(dictionary)
	return np.asarray(matrix), episodes, dictionary, reverse_dictionary

def build_idf(matrix):
	binary_matrix = np.matrix(matrix, dtype=bool)*1
	rows, N = binary_matrix.shape
	array_idf = np.log(rows / (1 + (np.ones([1,rows]).dot(binary_matrix))))
	matrix_idf = np.tile(array_idf,(rows,1))
	return matrix_idf


if __name__ == '__main__':
	#Pasta de onde os textos serao obtidos
	directory = "../episodesJSON/"
	path = "../DATASET/episode_text.txt"
	matrix_tf, episodes, dictionary, reverse_dictionary = build_tf(path, directory)
	print "MATRIZ TF:"
	print matrix_tf,'\n\n'
	
	print "MATRIZ IDF:"
	matrix_idf = build_idf(matrix_tf)
	print matrix_idf,'\n\n'

	print "MATRIZ TF-IDF:"
	matrix_tfidf = np.multiply(matrix_tf, matrix_idf)
	print matrix_tfidf