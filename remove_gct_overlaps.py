import sys
import tempfile
import argparse
import os
#import ../lib/sort
#import ../lib/parse_gct
import sort
import parse_gct
import pdb

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def main(f_in=sys.stdin, f_out=sys.stdout):
	# 1 parse, 2 sort, 3 iterate/combine
	# first, get number of lines
	line=f_in.readline()
	line=f_in.readline()
	# 1. parse
	f_parsed=tempfile.NamedTemporaryFile(mode='w', delete=False)
	f_parsed_name=f_parsed.name
	#f_parsed.close()
	parse_gct.main(f_in, f_parsed)
	f_parsed.close()
	f_parsed=open(f_parsed_name, 'r')
	num_rows=int(wc.wc(f_parsed, 'lines'))-1

	# 2. sort
	f_sorted=tempfile.NamedTemporaryFile(mode='w', delete=False)
	f_sorted_name=f_sorted.name
	f_sorted.close()
	sort.batch_sort(f_parsed_name, f_sorted_name)

	# 3. iterate/combine
	f_sorted=open(f_sorted_name, 'r')
	f_combined=f_out
	prev_line=''
	prev_cols=[]
	num_cols=0
	for line in f_sorted:
		if not num_cols:
			f_combined.write(line)
			num_cols=len(line.split('\t'))
		else:
			cols=line.split('\t')	# keep \n at end of line
			lc=len(cols)
			if lc<num_cols:
				cols=cols[0:lc-2] + ['']*(num_cols-lc) + cols[lc-2:]
			if prev_line!='':
				# same chrom, and prev end >= curr start --> overlap!
				if prev_cols[0]==cols[0] and prev_cols[2]>=cols[1]:
					if args.verbose:
						sys.stderr.write('Overlap detected: ' + str([prev_cols[0:3], cols[0:3]])+ '\n')
					f_combined.write('\t'.join([prev_cols[0], prev_cols[1], '%09d'%(int(cols[1])-1)] + prev_cols[3:]))
					f_combined.write('\t'.join([prev_cols[0], cols[1], prev_cols[2]]))
					for col_id in range(3, num_cols-2):
						if is_number(cols[col_id]):
							if is_number(prev_cols[col_id]):
								f_combined.write('\t' + str((float(prev_cols[col_id])+float(cols[col_id]))/2))
							else:
								f_combined.write('\t' + cols[col_id])
						else:	# regardless of if prev_cols has a value, output that
							f_combined.write('\t' + prev_cols[col_id])
					num_rows+=1
					f_combined.write('\t' + str(num_rows))	# Record ID
					f_combined.write('\t' + prev_cols[-1])
					# update curr start to reflect a partial write
					cols[1]='%09d'%(int(prev_cols[2])+1)
				else:
					# cols may have changed from above, so output from that instead of straight from line
					f_combined.write('\t'.join(prev_cols))
			prev_line=line
			prev_cols=cols
	# at the end, the last line remains to be written
	f_combined.write('\t'.join(prev_cols))
	f_sorted.close()
	f_combined.flush()

	# cleanup
	os.remove(f_parsed_name)
	os.remove(f_sorted_name)

if __name__=='__main__':
	# arguments
	parser = argparse.ArgumentParser(description=
		'Combine overlapping segments within a GCT file.\n'
		'Outputs a tab-delimited file, not a valid GCT file.')
	parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='GCT file to fix')
	parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='output tab-delimited, non-GCT file without overlaps')
	parser.add_argument('--verbose', help='increase output verbosity', action='store_true')
	args = parser.parse_args()
	
	main(args.input, args.output)
