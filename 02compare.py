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

def read_new_line(fp_rnl):
	line=fp_rnl.readline().strip()
	if line:
		done_analyzing=False
		cols=line.split('\t')
		vals=cols[2:]
		chromRE=r'\|@chr([^:]*):'
		chrom_match=re.search(chromRE, cols[1])
		chrom=chrom_match.group(1)
		startRE=r'\|@[^:]*:([^-]*)-'
		start_match=re.search(startRE, cols[1])
		start=start_match.group(1)
		endRE=r'\|@[^:]*:[^-]*-([^|]*)\|'
		end_match=re.search(endRE, cols[1])
		end=end_match.group(1)
		if is_int(chrom) and is_int(start) and is_int(end):
			if int(start or -1)>int(end or -1):
				start, end = end, start
		else:
			chrom=-1
			start=-1
			end=-1
	else:
		done_analyzing=True
		vals=[]
		chrom=-1
		start=-1
		end=-1
	return (done_analyzing, line, vals, int(chrom or -1), int(start or -1), int(end or -1))

def read_new_line2(fp_rnl2):
	line=fp_rnl2.readline().strip()
	if line:
		done_analyzing=False
		cols=line.split('\t')
		vals=cols[3:]
		chrom=cols[0]
		start=cols[1]
		end=cols[2]
		if is_int(chrom) and is_int(start) and is_int(end):
			if int(start or -1)>int(end or -1):
				start, end = end, start
		else:
			chrom=-1
			start=-1
			end=-1
	else:
		done_analyzing=True
		vals=[]
		chrom=-1
		start=-1
		end=-1
	return (done_analyzing, line, vals, int(chrom or -1), int(start or -1), int(end or -1))

# constants
sort_path=r'c:\program files (x86)\gnuwin32\bin\sort.exe'

# arguments
parser = argparse.ArgumentParser(description='Compare multiple GCT files from different array design files. Average individual samples equally, not files.')
parser.add_argument('inputs', nargs='+', help='sorted GCT files to compare')
parser.add_argument('--verbose', help='increase output verbosity', action='store_true')
args = parser.parse_args()

# open inputs and initialize values; also create temp sorted version
num_files=len(args.inputs)
fps=[]
fp_temps=[]
fp_temp_names=[]
f_num_series=[]
num_series=0
series_names=[]	# will be a non-rectangular 2D list of series names, series_names[fileID][seriesID]
#done_analyzing=[]
num_files_to_analyze=num_files
for f_name in args.inputs:
	# open
	fp=open(f_name, 'r')
	fps.append(fp)
	fp_temps.append(tempfile.NamedTemporaryFile(mode='w+', delete=False))
	fp_temp_names.append(fp_temps[-1].name)
	# calc num_series
	thisf_num_series=0
	line_num=0
	line=fp.readline()	# #2.1
	line=fp.readline()	# rows, columns
	line=fp.readline().strip()	# header row
	cols=line.split('\t')
	fp_temps[-1].write('Chrom\tStart\tEnd')
	series_names.append([])
	for cc in cols[2:]:	# ignore 'Reporter Number' and 'Description'
		if cc!='Average':
			num_series+=1
			thisf_num_series+=1
			series_names[-1].append(cc)
			fp_temps[-1].write('\t' + cc)
	f_num_series.append(thisf_num_series)
	if args.verbose:
		sys.stderr.write(f_name + '/' + fp_temp_names[-1] + ' contains ' + str(thisf_num_series) + ' series\n')
	(done_analyzing, line, cols, chrom, start, end) = read_new_line(fp)
	while not done_analyzing:
		if is_int(chrom) and is_int(start) and is_int(end) and chrom>-1 and start>-1 and end>-1:
			num_found=False
			for cc in range(0, thisf_num_series):
				if is_number(cols[cc]):
					num_found=True
					break
			if num_found:
				fp_temps[-1].write('\n%(chrom)02d\t%(start)09d\t%(end)09d' % \
						{"chrom": chrom, "start": start, "end": end})
				for cc in range(0, thisf_num_series):
					if is_number(cols[cc]):
						fp_temps[-1].write('\t' + cols[cc])
					else:
						fp_temps[-1].write('\t')
		(done_analyzing, line, cols, chrom, start, end) = read_new_line(fp)
	fp.close()
	fp_temps[-1].close()
if args.verbose:
	sys.stderr.write('In total, ' + str(num_series) + ' series found\n')

# sort refactored inputs and remove overlaps between successive lines
done_analyzing=[]
for f_id in range(0, num_files):
	call([sort_path, '-n', fp_temp_names[f_id], '-o', fp_temp_names[f_id] + '1'])
	fps[f_id]=open(fp_temp_names[f_id] + '1', 'r')
	fp_temps[f_id]=open(fp_temp_names[f_id] + '2', 'w+')
	# initialize done_analyzing
	done_analyzing.append(False)
	prev_line=''
	prev_cols=[]
	for line in fps[f_id]:
		cols=line.strip().split('\t')
		if not is_int(cols[0]):
			num_cols=len(cols)
			fp_temps[f_id].write(line.strip())
		else:
			if len(cols)<num_cols:
				for i in range(len(cols), num_cols):
					cols.append('')
			if prev_line:
				if int(cols[0])==int(prev_cols[0]) and int(cols[2])<=int(prev_cols[1]):	# overlap with previous line
					if args.verbose and False:
						sys.stderr.write('Fixing overlap within file ' + str(f_id) + '.\n')
						sys.stderr.write(prev_line)
						sys.stderr.write(line)
						sys.stderr.write(str([prev_cols[0], prev_cols[1], int(cols[1])-1]) + '\n')
						sys.stderr.write(str([prev_cols[0], cols[1], prev_cols[2]]) + '\n')
					fp_temps[f_id].write('\n%(chrom)02d\t%(start)09d\t%(end)09d' % \
							{'chrom': int(prev_cols[0]), \
							'start': int(prev_cols[1]),\
							'end': int(cols[1])-1})
					for cc in range(3,num_cols):
						fp_temps[f_id].write('\t' + prev_cols[cc])
					fp_temps[f_id].write('\n%(chrom)02d\t%(start)09d\t%(end)09d' % \
							{'chrom': int(prev_cols[0]), \
							'start': int(cols[1]),\
							'end': int(prev_cols[2])})
					for cc in range(3,num_cols):
						if is_number(prev_cols[cc]):
							if is_number(cols[cc]):
								fp_temps[f_id].write('\t' + str((float(prev_cols[cc])+float(cols[cc]))/2))
							else:
								fp_temps[f_id].write('\t' + prev_cols[cc])
						else:
							fp_temps[f_id].write('\t' + cols[cc])
					cols[1]=prev_cols[2]+1
				else:
					fp_temps[f_id].write('\n%(chrom)02d\t%(start)09d\t%(end)09d' % \
							{'chrom': int(prev_cols[0]), \
							'start': int(prev_cols[1]),\
							'end': int(prev_cols[2])})
					for cc in range(3,num_cols):
						fp_temps[f_id].write('\t' + prev_cols[cc])
			prev_line=line
			prev_cols=cols
	fp_temps[f_id].write('\n%(chrom)02d\t%(start)09d\t%(end)09d' % \
			{'chrom': int(prev_cols[0]), \
			'start': int(prev_cols[1]),\
			'end': int(prev_cols[2])})
	for cc in range(3,num_cols):
		fp_temps[f_id].write('\t' + prev_cols[cc])
	fps[f_id].close()
	fp_temps[f_id].seek(0,0)

fps=fp_temps
# headers
gct_temp=tempfile.NamedTemporaryFile(mode='w+', delete=False)
#gct_temp.write('#2.1')
#gct_temp.write('\n\t' + str(num_series+1))
gct_temp.write('Reporter Identifier\tDescription')
for f_id in range(0, num_files):
	for series_name in series_names[f_id]:
		gct_temp.write('\t' + series_name)
gct_temp.write('\tAverage')

# grab the first line of data from each file
lines=[]
vals=[]
chroms=[]
starts=[]
ends=[]
for f_id in range(0, num_files):
	fp=fps[f_id]
	lines.append('')
	vals.append([])
	chroms.append(0)
	starts.append(0)
	ends.append(0)
	(done_analyzing[f_id], lines[-1], vals[-1], chroms[-1], starts[-1], ends[-1]) = read_new_line2(fp)
	while not done_analyzing[f_id] and (chroms[-1]==-1 or starts[-1]==-1 or ends[-1]==-1):
		(done_analyzing[f_id], lines[-1], vals[-1], chroms[-1], starts[-1], ends[-1]) = read_new_line2(fp)

row_id=0
while num_files_to_analyze:
	row_id+=1
	# find lowest start and sequence end
	chrom_curr=-1
	start_min=-1
	end_curr=-1
	for f_id in range(0, num_files):
		if done_analyzing[f_id]:
			continue
		#----------------------|-------A-------|----------------------
		#    | <- B1a
		#    |----B1----|
		#           |----B2----|
		#                      |  <- B2a
		#               |----B3----|
		#               |----------B4----------|
		#               |----------------B5----------------|
		#                      |----B6----|
		#----------------------|-------A-------|----------------------
		#                      |------B7-------|
		#                      |----------B8-----------|
		#                         |----B9----|
		#                         | <- B9a
		#                         |----B10-----|
		#                         |--------B11--------|
		#                              B11a -> |
		#                                      |----B12----|
		#                                         |----B13----|
		#                                         | <- B13a
		#----------------------|-------A-------|----------------------
		if start_min==-1:	# uninitialized
			chrom_curr=chroms[f_id]
			start_min=starts[f_id]
			end_curr=ends[f_id]
		elif chroms[f_id]<chrom_curr:
			chrom_curr=chroms[f_id]
			start_min=starts[f_id]
			end_curr=ends[f_id]
		elif chroms[f_id]==chrom_curr:
			if end_curr==starts[f_id] and starts[f_id]==ends[f_id]:	# B11a
				end_curr-=1
			elif ends[f_id]<start_min:	# B1 & B1a
				start_min=starts[f_id]
				end_curr=ends[f_id]
			elif ends[f_id]==start_min and starts[f_id]<start_min:	# B2
				start_min=starts[f_id]
				end_curr=ends[f_id]-1
			elif ends[f_id]==start_min and starts[f_id]==start_min:	# B2a
				end_curr=start_min
			elif starts[f_id]<start_min and ends[f_id]>start_min and ends[f_id]<end_curr:	# B3
				end_curr=start_min-1
				start_min=starts[f_id]
			elif starts[f_id]<start_min and ends[f_id]==end_curr:	# B4
				end_curr=start_min-1
				start_min=starts[f_id]
			elif starts[f_id]<start_min and ends[f_id]>end_curr:	# B5
				end_curr=start_min-1
				start_min=starts[f_id]
			elif starts[f_id]==start_min and ends[f_id]<end_curr:	# B6
				end_curr=ends[f_id]
			# B7 = no change
			# B8 = no change
			elif starts[f_id]>start_min and starts[f_id]<=end_curr:	# B9, B9a, B10, B11, B11a, B12
				end_curr=starts[f_id]-1
			# B13, B13a = no change
	# output row
	if args.verbose and False:
		sys.stderr.write(str([chrom_curr, start_min, end_curr]) + '\n')
	gct_temp.write('\n' + str(row_id) + '\t' + 
			'na |@chr' + str(chrom_curr) + ':' + str(start_min) + '-' + str(end_curr) + '|')
	sum=0
	sum_count=0
	for f_id in range(0, num_files):
		# if there is overlap, output values and add to average (length-weighted)
		# otherwise just empty space
		if not done_analyzing[f_id] and chrom_curr==chroms[f_id] and start_min<=ends[f_id] and starts[f_id]<=ends[f_id]:
			# possibilities are:
			#----------------------|-------A-------|----------------------
			#                      |------B7-------|
			#                      |----------B8-----------|
			for s_id in range(0, f_num_series[f_id]):
				if args.verbose and False:
					sys.stderr.write(str([f_id, s_id]) + '\n')
				if len(vals[f_id])<=s_id or not is_number(vals[f_id][s_id]):
					gct_temp.write('\t')
				else:
					gct_temp.write('\t' + vals[f_id][s_id])	# skip reporter ID and description
					sum_count+=1
					if args.verbose and False:
						sys.stderr.write(str([f_id, s_id, vals[f_id][s_id]]) + '\n')
					sum+=float(vals[f_id][s_id])
			if ends[f_id]==end_curr:	# time to get new line?
				(done_analyzing[f_id], lines[f_id], vals[f_id], chroms[f_id], starts[f_id], ends[f_id]) = read_new_line2(fps[f_id])
				while not done_analyzing[f_id] and (chroms[f_id]==-1 or starts[f_id]==-1 or ends[f_id]==-1):
					(done_analyzing[f_id], lines[f_id], vals[f_id], chroms[f_id], starts[f_id], ends[f_id]) = read_new_line2(fps[f_id])
				if done_analyzing[f_id]:
					num_files_to_analyze-=1
					fps[f_id].close()
			else:	# update start & end of current file
				starts[f_id]=end_curr+1
		else:
			for s_id in range(0, f_num_series[f_id]):
				gct_temp.write('\t')
	gct_temp.write('\t' + str(sum/sum_count))

gct_temp_name=gct_temp.name
gct_temp.close()
gct_temp=open(gct_temp_name, 'r')
sys.stdout.write('#2.1')
sys.stdout.write('\n' + str(row_id) + '\t' + str(num_series+1) + '\n')
for line in gct_temp:
	sys.stdout.write(line)
gct_temp.close()

for f_id in range(0, num_files):
	os.remove(fp_temp_names[f_id])
	os.remove(fp_temp_names[f_id] + '1')
	os.remove(fp_temp_names[f_id] + '2')
os.remove(gct_temp_name)
