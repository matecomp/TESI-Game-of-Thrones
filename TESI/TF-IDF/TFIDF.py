# -*- coding: utf-8 -*-
import nltk
import re
import collections
import numpy as np
import pandas as pd
import operator
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
	files = [sorted(file) for file in files]
	files = sorted(files)
	return files

#Stemmer for all words in vocabulary
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer("english")

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

def load(filename,name,numpy=False):
    """Carrega os dados de alguma rede anteriormente treinada."""
    f = open(filename, "r")
    data = json.load(f)
    f.close()
    if numpy:
    	data_array = [np.array(w) for w in data[name]]
    	data_array = np.asarray(data_array)
    else:
    	data_array = [w for w in data[name]]
    return data_array

def save(filename,name,archive,numpy=False):
    """Salva os valores do vies e dos pesos da rede num arquivo."""
    filename = filename
    if numpy:
    	data = {name: [v.tolist() for v in archive]}
    else:
    	data = {name: [v for v in archive]}
    f = open(filename, "w")
    json.dump(data, f)
    f.close()

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
	text = ""
	for p in paragraph:
		text += p['location'] + '\n'
		text += p['content'] + '\n'
	text += data_json['info'] + '\n'
	text += data_json['plot'] + '\n'
	text = preprocessing(text)
	return text

def word2freq(content):
	words = nltk.word_tokenize(content)
	words = removeStopwords(words)
	words = [stemmer.stem(word) for word in words]
	data, count, dictionary, reverse_dictionary = build_dataset(words)
	return count, dictionary, reverse_dictionary

def build_tf(path, directory):
	#Extrai o corpus de GoT
	f = open(path, "rb")
	episode_text = f.read()
	f.close()


	#Monta o vocabulirio contando todo todas as palavras do corpus
	#Obs: devido as marcacoes contendo as localicoes e titulos, temos que remover antes de montar o TF
	episode_text = preprocessing(episode_text)
	_, dictionary, reverse_dictionary = word2freq(episode_text)

	episodes = list()

	m = len(dictionary)
	matrix = np.zeros([0,m])
	
	seasons = list_files(directory)
	for season in seasons:
		for episode in season:
			episode_name = episode.split('/')[-1]
			print "Processing: ", episode_name
			episodes.append(episode_name)			
			data_json = openJson(episode)
			content = Json2Content(data_json)
			#Obs: devido as marcacoes contendo as localicoes e titulos, temos que remover antes de montar o TF
			content = re.sub(r"<.+>", "", content)
			count, _, _  = word2freq(content.lower())
			vector = np.zeros([1,m])
			for word, freq in count:
				col = dictionary[word]
				vector[0,col] = freq
			matrix = np.vstack([matrix,vector])
	return np.asarray(matrix), episodes, dictionary, reverse_dictionary

def build_idf(matrix):
	binary_matrix = np.matrix(matrix, dtype=bool)*1
	rows, N = binary_matrix.shape
	array_idf = np.log(rows / (1 + (np.ones([1,rows]).dot(binary_matrix))))
	matrix_idf = np.tile(array_idf,(rows,1))
	return np.asarray(matrix_idf)

def addLabels(matrix, episodes, dictionary):
	documents = episodes
	terms = dictionary
	new_matrix = pd.DataFrame(matrix, index=terms, columns=documents)
	return new_matrix

def train(path, directory, loadTFIDF=False, prints=True, log_prints=False):
	if loadTFIDF:
		# matrix_tfidf = pd.read_csv("matrixTFIDF/matrix_tfidf.csv", sep=' ')
		matrix_tfidf = load("matrixTFIDF/matrix_tfidf.json", "matrix_tfidf", numpy=True)
		dictionary = load("matrixTFIDF/dictionary.json", "dictionary")
		reverse_dictionary = load("matrixTFIDF/reverse_dictionary.json", "reverse_dictionary")
		episodes = load("matrixTFIDF/episodes.json", "episodes")
		dictionary = {name: idx for idx,name in enumerate(dictionary)}
		# print dictionary
	else:
		matrix_tf, episodes, dictionary, reverse_dictionary = build_tf(path, directory)
		if log_prints:
			print "MATRIZ TF:"
			print matrix_tf,'\n\n'
		
		matrix_idf = build_idf(matrix_tf)
		if log_prints:
			print "MATRIZ IDF:"
			print matrix_idf,'\n\n'

		matrix_tfidf = matrix_tf * matrix_idf
		# matrix_tfidf = np.multiply(matrix_tf, matrix_idf)
		if log_prints:
			print "MATRIZ TF-IDF:"
			print matrix_tfidf

		# Matrix: terms x documents
		matrix_tfidf = matrix_tfidf.T

		print matrix_tfidf.shape
		vocabulary = [word for word, _ in sorted(dictionary.items(), key=operator.itemgetter(1))]
		save("matrixTFIDF/dictionary.json", "dictionary", vocabulary)
		save("matrixTFIDF/reverse_dictionary.json", "reverse_dictionary", reverse_dictionary)
		save("matrixTFIDF/episodes.json", "episodes", episodes)
		save("matrixTFIDF/matrix_tfidf.json", "matrix_tfidf", matrix_tfidf, numpy=True)
		matrix_tfidf2 = addLabels(matrix_tfidf, episodes, dictionary)
		matrix_tfidf2.to_csv("matrixTFIDF/matrix_tfidf.csv", index=True, header=True, sep=' ')

	if prints:
		print matrix_tfidf

	return matrix_tfidf, dictionary, reverse_dictionary, episodes

def search(words, shape, dictionary, weight, matrix, matrix_trans=None, svd=None):
	terms, docs = shape
	consult = np.zeros([terms])
	words = [stemmer.stem(word) for word in words]
	ids = [dictionary[word] for word in words]
	consult[ids] = weight
	
	if svd is not None:
		consult = consult.dot(matrix_trans)

	dist = consult.dot(matrix)
	ans = np.argsort(-dist)
	print "The answer is:"
	for i in xrange(5):
		print episodes[ans[i]]

from sklearn.decomposition import TruncatedSVD
#Provavelmente tem de transpor
def build_svd(matrix_tfidf):
	svd = TruncatedSVD(n_components=10, n_iter=7, random_state=42)
	svd.fit(matrix_tfidf)
	terms_k = svd.transform(matrix_tfidf)
	docs_k = svd.components_
	return svd, terms_k, docs_k



if __name__ == '__main__':
	#Pasta de onde os textos serao obtidos
	directory = "../episodesJSON/"
	path = "../DATASET/episode_text.txt"
	loadTFIDF = True
	prints = False
	#SHAPE: [55 x 5111]
	#SHAPE STEMMER: [55 x 3693]
	matrix_tfidf, dictionary, _, episodes = train(path, directory, loadTFIDF=loadTFIDF, prints=prints, log_prints=False)
	shape = matrix_tfidf.shape

	print "Search on matrix-tfidf:"
	print shape
	wordlist = ["joffrey","kill","eddard","cry"]
	search(wordlist, shape, dictionary, 1.0, matrix_tfidf)
	svd, terms_k, docs_k = build_svd(matrix_tfidf)

	print "\n\n"
	
	print "Search on SVD matrix:"
	print svd.components_.shape
	search(wordlist, shape, dictionary, 1.0, docs_k, terms_k, svd=svd)
	