# -*- coding: utf-8 -*-
import collections
import nltk
import csv
import re

def loadCSV(archive):
	group = set()
	with open(archive, 'rb') as csvfile:
		words = csv.reader(csvfile)
		for word in words:
			if word[0] != "NER":
				group.update(word)
	return group

def normalizeNER(archive):
	#Extrai o corpus de GoT
	f = open(archive, "rb")
	episode_text = f.read()
	f.close()
	
	#Extrai as entidades nomeadas obtidas em extractNE
	NE = loadCSV("../NER/Naive-NER.csv")
	NE = [name.upper() for name in NE]

	buffer = collections.deque(maxlen=100)
	lines = episode_text.split('\n')
	line_token = [nltk.word_tokenize(line) for line in lines]

	output = ""

	temp_word = ""
	for line in line_token:
		for word in line:
			if word.isupper() and word.isalpha() and temp_word + word in NE:
				temp_word += word + " "
			else:
				if temp_word != "":
					occurrences = [ent for ent in buffer if temp_word in ent and temp_word != ent]
					if len(occurrences) > 0:
						temp_word = occurrences[-1]
					# else:
					# 	candidates = [ent for ent in NE if temp_word in ent]
					# 	candidates = sorted(candidates, reverse=True)
					# 	if len(candidates) > 0:
					# 		temp_word = candidates[0]
					buffer.append(temp_word)
					output += temp_word + " "
				if word.isupper():
					temp_word = word + " "
				else:
					output += word + " "
					temp_word = ""
		output += '\n'

	output = re.sub(r" +$", "", output)
	output = re.sub(r" +", " ", output)
	output = re.sub(r" '","'", output)
	output = re.sub(r" 'S","'S", output)
	
	f = open("../DATASET/teste.txt", "wb")
	f.write(output)
	f.close()

	return output


if __name__ == '__main__':
	text = normalizeNER("../DATASET/dataset.txt")


