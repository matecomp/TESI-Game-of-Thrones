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
	NE = loadCSV("../NER/ENTITIES/Naive-NER.csv")
	NE = [entity.upper() for entity in NE]
	freqNE = {entity : episode_text.count(entity) for entity in NE}

	buffer = collections.deque(maxlen=200)
	lines = episode_text.split('\n')
	line_token = [nltk.word_tokenize(line) for line in lines]

	output = ""

	temp_word = ""
	for line in line_token:
		for word in line:
			word = re.sub(r" ", "", word)
			flag1 = True if temp_word + word in NE else False
			flag2 = True if word + " " in NE else False
			flag = flag2 if temp_word == "" else flag1
			if word.isupper() and word.isalpha() and flag:
				temp_word += word + " "
			else:
				if temp_word != "":
					occurrences = [ent for ent in buffer if temp_word in ent and temp_word != ent]
					if len(occurrences) > 0:
						temp_word = occurrences[-1]
					buffer.append(temp_word)
					temp_word = re.sub(r" +$", "", temp_word)
					output += " <" + temp_word + "> " if temp_word in NE else temp_word.lower() + " "
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
	
	f = open("../DATASET/normalizeNE.txt", "wb")
	f.write(output)
	f.close()

	return output


if __name__ == '__main__':
	text = normalizeNER("../DATASET/dataset.txt")


