# based on Recipe 466302: Sorting big files the Python 2.4 way
# by Nicolas Lehuen

import os
from tempfile import gettempdir
from itertools import islice, cycle
from collections import namedtuple
import heapq
import pdb
import sys

Keyed = namedtuple("Keyed", ["key", "obj"])

def merge(key=None, *iterables):
	# based on code posted by Scott David Daniels in c.l.p.
	# http://groups.google.com/group/comp.lang.python/msg/484f01f1ea3c832d

	if key is None:
		keyed_iterables = iterables
	else:
		keyed_iterables = [(Keyed(key(obj), obj) for obj in iterable)
							for iterable in iterables]
	for element in heapq.merge(*keyed_iterables):
		yield element

def batch_sort(input_file, output_file, key=None, buffer_size=32000, tempdirs=None):
	lines = input_file.readlines()
	lines.sort()
	for line in lines:
		output_file.write(line)

def batch_sort_PREV(input_file, output_file, key=None, buffer_size=32000, tempdirs=None):
	if tempdirs is None:
		tempdirs = []
	if not tempdirs:
		tempdirs.append(gettempdir())

	chunks = []
	try:
		input_iterator = iter(input_file)
		for tempdir in cycle(tempdirs):
			current_chunk = list(islice(input_iterator,buffer_size))
			if not current_chunk:
				break
			current_chunk.sort(key=key)
			output_chunk = open(os.path.join(tempdir,'%06i'%len(chunks)),'w+b',64*1024)
			chunks.append(output_chunk)
			for line in current_chunk:
				output_chunk.write(line)
			output_chunk.flush()
			output_chunk.seek(0)
		output_file.writelines(merge(key, *chunks))
	finally:
		for chunk in chunks:
			try:
				chunk.close()
				os.remove(chunk.name)
			except Exception:
				pass


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(
		description='Sort a file in accordance with the parameters provided.')

	parser.add_argument(
		'input',
		nargs='?',
		type=argparse.FileType('r'),
		default=sys.stdin)

	parser.add_argument(
		'output',
		nargs='?',
		type=argparse.FileType('r'),
		default=sys.stdout)

	parser.add_argument(
		'-b','--buffer',
		dest='buffer_size',
		type=int,default=32000,
		help='''Size of the line buffer. The file to sort is
			divided into chunks of that many lines. Default : 32,000 lines.'''
	)
	parser.add_argument(
		'-k','--key',
		dest='key',
		help='''Python expression used to compute the key for each
			line, "lambda line:" is prepended.\n
			Example : -k "line[5:10]". By default, the whole line is the key.'''
	)
	parser.add_argument(
		'-t','--tempdir',
		dest='tempdirs',
		action='append',
		default=[],
		help='''Temporary directory to use. You might get performance
			improvements if the temporary directory is not on the same physical
			disk than the input and output directories. You can even try
			providing multiples directories on differents physical disks.
			Use multiple -t options to do that.'''
	)
	parser.add_argument(
		'-p','--psyco',
		dest='psyco',
		action='store_true',
		default=False,
		help='''Use Psyco.'''
	)
	#options,args = parser.parse_args()
	args=parser.parse_args()

	if args.key:
		args.key = eval('lambda line : (%s)'%args.key)

	if args.psyco:
		import psyco
		psyco.full()

	batch_sort(args.input, args.output, args.key, args.buffer_size, args.tempdirs)
	# if executing from another Python script, execute 'sort.batch_sort([input], [output], [False | eval('lambda line : line[5:10]')], 32000, [])'
	#
	# [input] = path to the input file
	# [output] = path to the output file
	# [False | eval('lambda line : line[5:10]')] = False if the entire line should be used for sorting or <something unknown>
	# 32000 = buffer size (number of lines)
	# [] = temp dir list
