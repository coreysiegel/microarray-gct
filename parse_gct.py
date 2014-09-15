import re
import sys
import argparse

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# takes in a proper GCT file and outputs a sortable file
# chrom, start, end, values, record id, description (without chrom/start/end info)
def main(fin=sys.stdin, fout=sys.stdout):
	chromRE=r'\|@chr([^:]*):'
	startRE=r'\|@[^:]*:([^-]*)-'
	endRE=r'\|@[^:]*:[^-]*-([^|]*)\|'
	descRE=r'(.*)\|@.*\|'

	row_id=0
	for line in fin:
		row_id+=1
		if row_id<3:
			continue
		else:
			cols=line.strip().split('\t')
			if row_id==3:
				fout.write('Chrom\tStart\tEnd')
				for cc in cols[2:]:
					fout.write('\t' + cc)
				fout.write('\tRecord Identifier\tDescription')
			else:
				vals=cols[2:]
				chrom_match=re.search(chromRE, cols[1])
				if not chrom_match:
					continue
				chrom=chrom_match.group(1)
				start_match=re.search(startRE, cols[1])
				if not start_match:
					continue
				start=start_match.group(1)
				end_match=re.search(endRE, cols[1])
				if not end_match:
					continue
				end=end_match.group(1)
				desc_match=re.search(descRE, cols[1])
				if not desc_match:
					continue
				desc=desc_match.group(1).strip()
				if is_int(chrom) and is_int(start) and is_int(end):
					if int(start or -1)>int(end or -1):
						start, end = end, start
				else:
					continue
				containsVal=False
				for vv in vals:
					if is_number(vv):
						containsVal=True
						break
				if not containsVal:
					continue
				if desc=='':
					desc='na'
				fout.write('\n' + '\t'.join([
					'%(chrom)03d' % {'chrom' : int(chrom or -1)},
					'%(start)09d' % {'start' : int(start or -1)},
					'%(end)09d' % {'end' : int(end or -1)}] +
					vals +
					[cols[0],
					desc]))

if __name__ == '__main__':
	parser=argparse.ArgumentParser()
	parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument('output', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
	args=parser.parse_args()
	main(args.input, args.output)
