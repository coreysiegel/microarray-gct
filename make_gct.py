# called from another program, use makeGCT.make(input, output)
# input should have one header row followed by data
# input should be tab-delimited, [chrom, start, end, values, record id, description]
import argparse
import sys
import wc
import pdb
import tempfile

def make(f_in=sys.stdin, f_out=sys.stdout):
	if f_in==sys.stdin:
		f_temp=tempfile.NamedTemporaryFile(mode='w', delete=False)
		f_temp_name=f_temp.name
		for line in f_in:
			f_temp.write(line)
		f_temp.close()
	else:
		f_temp_name=f_in.name
	#pdb.set_trace()
	linecount=wc.wc(open(f_temp_name), 'lines')
	linecount=int(linecount)-1
	# determine number of blank lines
	f_in=open(f_temp_name, 'r')
	for line in f_in:
		if len(line)==0:
			linecount-=1
	f_in.close()
	f_out.write('#2.1')
	f_in=open(f_temp_name, 'r')
	num_cols=0
	for line in f_in:
		cols=line.strip().split('\t')
		if num_cols==0:
			num_cols=len(cols)
			f_out.write('\n' + '\t'.join([str(linecount), str(num_cols-5)]))
			f_out.write('\n' + '\t'.join(cols[-2:] + cols[3:-2]))
		else:
			f_out.write('\n' + '\t'.join(cols[-2:]) + ' |@chr' + cols[0] + ':' + cols[1] + '-' + cols[2] + '|')
			f_out.write('\t'.join([''] + cols[3:-2]))
			lc=len(cols)
			if lc<num_cols:
				pdb.set_trace()
				f_out.write('\t'.join(['']*(num_cols-lc+1)))
	
if __name__=='__main__':
	parser = argparse.ArgumentParser(description='Print the number of newlines, words, and bytes in files')
	parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='input file')
	parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='output GCT file')
	args = parser.parse_args()
	make(args.input, args.output)
