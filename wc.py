# called from another program, use wc.wc(<input>, bytes|chars|lines|max-line-length|words)
import argparse
import sys

def wc_bytes(f_in):
	c=0
	for i, l in enumerate(f_in):
		c+=len(l)
	return c
def wc_chars(f_in):
	return wc_bytes(f_in)
def wc_lines(f_in):
	for i, l in enumerate(f_in):
		pass
	return i + 1
def wc_max_line_length(f_in):
	c=0
	for i, l in enumerate(f_in):
		if len(l)>c:
			c=len(l)
	return c
def wc_words(f_in):
	return 0


def wc(f_in, option):
	option_lookup=['bytes', 'chars', 'lines', 'max-line-length', 'words']
	opt_id=option_lookup.index(option)
	fxn=[wc_bytes, wc_chars, wc_lines, wc_max_line_length, wc_words][opt_id]
	return fxn(f_in)

if __name__=='__main__':
	parser = argparse.ArgumentParser(description='Print the number of newlines, words, and bytes in files')
	parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument('-c', '--bytes', action='store_true', help='print the byte counts')
	parser.add_argument('-m', '--chars', action='store_true', help='print the character counts')
	parser.add_argument('-l', '--lines', action='store_true', help='print the newline counts')
	parser.add_argument('-L', '--max-line-length', action='store_true', help='print the length of the longest line')
	parser.add_argument('-w', '--words', action='store_true', help='print the word counts')
	args = parser.parse_args()
	
	options=[args.bytes, args.chars, args.lines, args.max_line_length, args.words]
	option_lookup=['bytes', 'chars', 'lines', 'max-line-length', 'words']
	num_options=sum(options)
	if num_options!=1:
		parser.print_usage(sys.stderr)
		sys.stderr.write('wc.py: error: exactly one option required\n')
		sys.exit(1)
	opt_loc=options.index(True)
	wc_out=wc(args.input, option_lookup[opt_loc])
	print(str(wc_out))
