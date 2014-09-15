import sys
import tempfile
import argparse
import re
from collections import defaultdict
import os.path
import pdb
from subprocess import call

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

def roman_to_arabic(s):
	romans = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
	arabic_number = 0
	st_roman_number = s.upper()
	lst_substract = []
	
	n = len(st_roman_number)
	for i in range(n-1):
	  ch = st_roman_number[i]
	  ch2 = st_roman_number[i+1]
	  if (romans[ch] < romans[ch2]):
	    lst_substract.append(i)
	for i in range(n):
	  ch = st_roman_number[i]
	  if (i in lst_substract):
	    arabic_number -= romans[ch]
	  else:
	    arabic_number += romans[ch]
	return arabic_number

# constants
re0_adf_start='^Reporter Name\t'
re1_adf_start=re.compile(re0_adf_start)
adf_params=defaultdict(list, {
	'filename': ['A-GEOD-6503.adf.txt', 'A-GEOD-8908.adf.txt', 'array design A GEOD 16281.txt'],
	'chrom': ['Comment[PROBE_ID]', 'Comment[systematic name]','Comment[Name]'],
	'chromNumerals': ['Arabic', 'Arabic', 'Roman'],
	'chromRE': [r'^chr([^_]*)_', r'^chr([^:]*):', r'^chr([^:]*):'],	# within the selected column
	'start': ['Comment[RANGE_START]', 'Comment[RANGE_START]', 'Comment[Name]'],
	'startRE': [r'(.*)', r'(.*)', r':([^-]*)-'],
	'end': ['Comment[RANGE_END]', 'Comment[RANGE_END]', 'Comment[Name]'],
	'endRE': [r'(.*)', r'(.*)', r'-(.*)'],
	'annotation': ['Reporter Comment', 'Comment[gene name]', 'Reporter Sequence']})
sort_path=r'c:\program files (x86)\gnuwin32\bin\sort.exe'

# arguments
parser = argparse.ArgumentParser(description='Combine array design file and ChIP output(s) to form GCT file.')
parser.add_argument('adf', help='filename of array design file')
parser.add_argument('sample_table', nargs='+', help='ChIP output sample tables')
parser.add_argument('--verbose', help='increase output verbosity', action='store_true')
args = parser.parse_args()

# determine ADF
try:
	adf_id=adf_params['filename'].index(os.path.basename(args.adf))
	if args.verbose:
		sys.stderr.write('adf_id=' + str(adf_id) + '\n')
except ValueError:
	raise NotImplementedError('This adf is not yet implemented.')

# refactor ADF into standard format
adf_fp=open(args.adf, 'r')	# attempt to open array design file
adf_temp=tempfile.NamedTemporaryFile(mode='w+', delete=False)	# attempt to open temp file for refactored adf
adf_temp_name=adf_temp.name
if args.verbose:
	sys.stderr.write('adf_temp_name=' + adf_temp_name + '\n')
adf_start_found=False
for line in adf_fp:
	if not adf_start_found and re1_adf_start.match(line):	# found header row
		adf_start_found=True
		if args.verbose:
			sys.stderr.write('ADF start found: ' + line + '\n')

		cols=line.strip().split('\t')
		if args.verbose:
			sys.stderr.write(str(cols) + '\n')
		try:
			chrom_col=cols.index(adf_params['chrom'][adf_id])
			if args.verbose:
				sys.stderr.write('chrom_col (' + adf_params['chrom'][adf_id] + ')=' + str(chrom_col) + '\n')
		except ValueError:
			raise Exception('Unable to find column "' + adf_params['chrom'][adf_id] + '" in adf file "' + args.adf + '"')
		try:
			start_col=cols.index(adf_params['start'][adf_id])
			if args.verbose:
				sys.stderr.write('start_col (' + adf_params['start'][adf_id] + ')=' + str(start_col) + '\n')
		except ValueError:
			raise Exception('Unable to find column "' + adf_params['start'][adf_id] + '" in adf file "' + args.adf + '"')
		try:
			end_col=cols.index(adf_params['end'][adf_id])
			if args.verbose:
				sys.stderr.write('end_col (' + adf_params['end'][adf_id] + ')=' + str(end_col) + '\n')
		except ValueError:
			raise Exception('Unable to find column "' + adf_params['end'][adf_id] + '" in adf file "' + args.adf + '"')
		try:
			annotation_col=cols.index(adf_params['annotation'][adf_id])
			if args.verbose:
				sys.stderr.write('annotation_col (' + adf_params['annotation'][adf_id] + ')=' + str(annotation_col) + '\n')
		except ValueError:
			raise Exception('Unable to find column "' + adf_params['annotation'][adf_id] + '" in adf file "' + args.adf + '"')
		
		adf_temp.write('\t'.join(['Reporter Name', 'Chrom', 'Start', 'End', 'Annotation']) + '\n')
		
	elif adf_start_found:	# processing actual data
		if args.verbose:
			sys.stderr.write(line)
		cols=line.strip().split('\t')
		reporter=cols[0]
		chrom_match=re.search(adf_params['chromRE'][adf_id], cols[chrom_col])
		if chrom_match:
			chrom_raw=chrom_match.group(1)
		else:
			continue	# not a valid chrom number
		if adf_params['chromNumerals'][adf_id]=='Arabic':
			chrom=chrom_raw
		elif adf_params['chromNumerals'][adf_id]=='Roman':
			chrom=roman_to_arabic(chrom_raw)
		else:
			raise Exception('Unknown numeral type for chrom:  ' + adf_params['chromNumerals'][adf_id])
		start_match=re.search(adf_params['startRE'][adf_id], cols[start_col])
		if start_match:
			start=start_match.group(1)
		else:
			continue	# not a valid start value
		if args.verbose:
			pdb.set_trace()
		end_match=re.search(adf_params['endRE'][adf_id], cols[end_col])
		if end_match:
			end=end_match.group(1)
		else:
			continue	# not a valid end value
		if start>end:
			start, end = end, start
		if annotation_col<len(cols) and cols[annotation_col]!='':
			annotation=cols[annotation_col]
		else:
			annotation=cols[chrom_col]
		str_out=('\t'.join([reporter, str(chrom), start, end, annotation]) + '\n')
		if args.verbose:
			sys.stderr.write('-> ' + str_out)
		adf_temp.write(str_out)


if not adf_start_found:
	raise Exception('Malformed adf; start not found with re ' + re0_adf_start)

adf_fp.close()
adf_temp.close()
call([sort_path, '-n', adf_temp_name, '-o', adf_temp_name + 'sor'])
adf_temp=open(adf_temp_name + 'sor', 'r')

# create predecessor GCT
gct_temp=tempfile.NamedTemporaryFile(mode='w+', delete=False)	# open temp file for gct in-progress
gct_temp_name=gct_temp.name
if args.verbose:
	sys.stderr.write('adf_temp_name=' + adf_temp_name + '\n')
num_samples=len(args.sample_table)
gct_temp.write('#2.1\n')
gct_temp.write('???\t' + str(1 if num_samples==1 else num_samples+1) + '\n')
gct_temp.write('Reporter Identifer\tDescription')	# do not add '\n' until samples are provided

samples=[]
line_s=[]
cols_s=[]
for st in args.sample_table:
	samples.append(open(st, mode='r'))	# attempt to open a sample table
	gct_temp.write('\t' + os.path.basename(st))
if num_samples>1:
	gct_temp.write('\tAverage')
gct_temp.write('\n')

unique_row_count=0
prev_reporter=-1

if args.verbose:
	sys.stderr.write('num_samples=' + str(num_samples) + '\n')
for s_id in range(0,num_samples):
	s=samples[s_id]
	line_s.append(s.readline().strip())
	if line_s[s_id][0:8]=='Reporter':
		line_s[s_id]=s.readline().strip()
	if line_s[s_id]:
		cols_s.append([])
		cols_s[s_id]=line_s[s_id].split('\t')
	else:
		raise Exception('Empty data file provided:  ' + s.name)
	if args.verbose:
		sys.stderr.write('s_id=' + str(s_id) + '\n')
		print('line_s=' + line_s[s_id])
		print('cols_s=' + str(cols_s[s_id]))
		print('')

for line_adf in adf_temp:
	if line_adf[0:8]=='Reporter':
		continue
	cols_adf=line_adf.strip().split('\t')
	if len(cols_adf)!=5:
		raise Exception('Unexpected number of columns in adf_temp\n"' + line_adf + '"')
	try:
		cols_adf_n=[]
		for i in range(0,4):
			cols_adf_n.append(int(cols_adf[i]))
	except ValueError:
		continue

	for s_id in range(0,num_samples):
		s=samples[s_id]
		while line_s[s_id] and (int(cols_s[s_id][0]) < cols_adf_n[0]):
			line_s[s_id]=s.readline().strip()
			if line_s[s_id]:
				cols_s[s_id]=line_s[s_id].split('\t')
		if line_s[s_id] and (int(cols_s[s_id][0]) == cols_adf_n[0]) and is_number(cols_s[s_id][1]):
			if prev_reporter != cols_adf_n[0]:
				prev_reporter=cols_adf_n[0]
				unique_row_count+=1
			gct_temp.write('\t'.join([cols_s[s_id][0],
				cols_adf[4] + ' |@chr' + cols_adf[1] + ':' + cols_adf[2] + '-' + cols_adf[3] + '|']))
			for i in range(0, s_id):
				gct_temp.write('\t')
			gct_temp.write('\t' + cols_s[s_id][1] + '\n')
			line_s[s_id]=s.readline().strip()
			if line_s[s_id]:
				cols_s[s_id]=line_s[s_id].split('\t')
if args.verbose:
	sys.stderr.write('Number of unique rows processed:  ' + str(unique_row_count) + '\n')

# make final GCT
gct_temp.seek(0,0)
line_gct=gct_temp.readline().strip()	# #2.1
print('#2.1')
line_gct=gct_temp.readline().strip()	# row/column count
print(str(unique_row_count) + '\t' + str(1 if num_samples==1 else num_samples+1))
if num_samples==1:
	line_gct=gct_temp.readline().strip()
	while line_gct:
		print(line_gct)
		line_gct=gct_temp.readline().strip()
else:
	values=[]
	values_active=[]
	for i in range(0, num_samples):
		values.append(0.)
		values_active.append(False)
	line_gct=gct_temp.readline().strip()	# headers
	sys.stdout.write(line_gct)
	line_gct=gct_temp.readline().strip()
	prev_reporter=-1
	while line_gct:
		cols_gct=line_gct.split('\t')
		r=int(cols_gct[0])
		desc=cols_gct[1]
		val=float(cols_gct[-1])
		val_loc=len(cols_gct)-3
		if args.verbose:
			sys.stderr.write(str([r, desc, val, val_loc, '\n']))
		if r!=prev_reporter:
			# finish previous line
			if prev_reporter!=-1:
				sys.stdout.write('\n' + str(prev_reporter) + '\t' + prev_desc)
				sum=0
				n=0
				for i in range(0, num_samples):	# output values and calculate average
					if values_active[i]:
						sum+=values[i]
						n+=1
						sys.stdout.write('\t' + str(values[i]))
					else:
						sys.stdout.write('\t')
				sys.stdout.write('\t' + str(sum/n))	# print average
			for i in range(0, num_samples):	# re-initialize values and active flags
				values[i]=0.
				values_active[i]=False
		values[val_loc]=val
		values_active[val_loc]=True
		prev_reporter=r
		prev_desc=desc
		line_gct=gct_temp.readline().strip()
	sys.stdout.write('\n' + str(prev_reporter) + '\t' + prev_desc)
	sum=0
	n=0
	for i in range(0, num_samples):	# output values and calculate average
		if values_active[i]:
			sum+=values[i]
			n+=1
			sys.stdout.write('\t' + str(values[i]))
		else:
			sys.stdout.write('\t')
	sys.stdout.write('\t' + str(sum/n))	# print average

for s in samples:
	s.close()

adf_temp.close()
os.remove(adf_temp_name)
os.remove(adf_temp_name + 'sor')
gct_temp.close()
os.remove(gct_temp_name)

if args.verbose:
	sys.stderr.write('End of implementation' + '\n')
