import os
import sys
from FastaReader import FastaReader
from DF import DF, DFWriter

from utils import versatile_open
open = versatile_open.versatile_open

def find_all_indices(seq, needle):
	result = []
	i = seq.find(needle)
	while i >= 0:
		result.append(i)
		i = seq.find(needle, i+1)
	return result

class Pyro:
	def __init__(self, name, fasta_filename, aln_length=None, rename_dups=False):
		"""
		if aln_length is not given then it is *guessed* by looking at the alignment in <fasta_filename>
		"""
		self.name = name
		self.rename_dups = rename_dups
		self.fasta_filename = fasta_filename
		self.fasta_reader = FastaReader(self.fasta_filename, self.rename_dups)
		if aln_length is None:
			key1 = self.fasta_reader.iterkeys().next()
			self.aln_length = len(self.fasta_reader[key1].seq)
		else:
			self.aln_length = aln_length
		self.nseq = len(self.fasta_reader.keys())

	def __getitem__(self, key):
		return self.fasta_reader[key]

	def keys(self):
		return self.fasta_reader.keys()

	def make_DF(self):
		df = DF(self.name, self.aln_length)
		for id in self.fasta_reader.iterkeys():
			r = self.fasta_reader[id]
			for nt in DF.nucleotides():
				# TODO: make find_all_indices iterative to be mem-efficient
				seq = r.seq.tostring().replace('U', 'T')
				positions = find_all_indices(seq, nt)
				df.add_to_vec(nt=nt, positions=positions, counts=[1]*len(positions))
#			for gapped_pos,nt in enumerate(r.seq):
#				df.add_to_vec(nt=nt, positions=[gapped_pos], counts=[1])
		return df

import random
from Sampler import Sampler
class PyroSampler(Sampler):
	def __init__(self, pyro):
		self.pyro = pyro

	def subsample(self, se):
		df = DF(self.pyro.name, self.pyro.aln_length)  
		keys = self.pyro.keys()
		for id in random.sample(keys, min(se, len(keys))):
			# to prevent "sample larger than population error" use min()
			r = self.pyro[id]
			for nt in DF.nucleotides():
				seq = r.seq.tostring().replace('U', 'T')
				positions = find_all_indices(seq, nt)
				df.add_to_vec(nt=nt, positions=positions, counts=[1]*len(positions))
			#for i,ecoli_pos in enumerate(SILVA.Ecoli1542_SILVA100):
				#df.add_to_vec(nt=r.seq[ecoli_pos], positions=[i], counts=[1])
		return df

if __name__ == "__main__":
	import glob
	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option("-p", "--pattern", dest="pattern", help="pattern for list of input files")
	parser.add_option("-o", "--output", dest="output", help="output filename (suffix should be .DF)")
	parser.add_option("--dup-ok", dest="rename_dups", action="store_true", default=False, help="ok to have duplicate IDs (renames them)")

	options, args = parser.parse_args()
	pattern, output = options.pattern, options.output

	f = open(output, 'w')
	w = DFWriter(f)
	for file in glob.iglob(pattern):
		print >> sys.stderr, "processing", file
		name = os.path.basename(file)
		pyro = Pyro(name, file, None, options.rename_dups)
		df = pyro.make_DF()
		w.write(df)
	f.close()

