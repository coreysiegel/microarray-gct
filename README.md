microarray-gct
==============
Python scripts for processing microarray data into GCT files, merging multiple GCT files, etc. Work in progress.

Routines
--------
1. convert microarray data into usable/plottable (GCT) form
	combine array design info (*.adf.txt) with microarray output:  (record, value) pair (*_sample_table.txt)
	create GCT file that maps values onto chromosomal positions
	multiple microarray output files (from a consistent array design) may be combined into a single GCT, at which point an "average" column will be added
	input (adf):  data begins row after "^Reporter Name"; first column (Reporter Name) is Reporter
		6503) Comment[PROBE_ID] has "chr#_.*" in Arabic numerals; Comment[RANGE_START] has start; Comment[RANGE_END] has end; Comment[SPOT_ID] has the gene name
		8908) Comment[systematic name] has "chr#:.*" in Arabic numerals; Comment[RANGE_START] has start; Comment[RANGE_END] has end; Comment[gene_name] has the gene name
		16281) Comment[Name] has "chr#:.*" in capitalized Roman numerals; Comment[Name] has ".*:#-.*" as start; Comment[Name] has ".*-#" as end; Reporter Sequence has the sequence
	input (sample table):  First column is Reporter; second column is value
	output (GCT):
		First row has "#1.2"
		Second row has "[record count]\t[sample count]"
		Third row has "Reporter Identifier\tDescription" + for each provided sample table, "\t[sample table name]" + if number of sample tables > 1, "\tAverage"
		Succeeding rows have data, "[Reporter]\t[gene name|sequence] |@chr[chrom #]:[start]-[end]" + for each sample table, "\t[value]" + if number of sample tables > 1, "\t[average of values]"; where all values are in Arabic numerals and values/averages are decimals
2. compare multiple microarray runs (GCT columns/files)
	for overlapping segments, average available values
	for segments with a value from one GCT file, provide that value
	for segments with no values from any GCT files, do not provide a value
	inputs may have a right-most "Average" column which should be ignored
	inputs may have multiple samples (columns right of "Description") which should be treated independently
	inputs:
		Third row:  "Reporter Identifier\tDescription" + for each provided sample table, "\t[sample table name]" + optionally [\tAverage]
		Fourth row:  "[^\t]*\t[^|]*|@chr[chrom #]:[start]-[end]" + for each sample table, "\t[value]" + if number of sample tables > 1, "\t[average of values]"; where all values are in Arabic numerals and values/averages are decimals
	output (GCT):
		First row has "#1.2"
		Second row has "[record count]\t[sample count]"
		Third row has "Reporter Identifier\tDescription" + for each provided table, "\t[sample name]" + "\tAverage"
		Succeeding rows have data, sorted by chr#, then start, with no overlapping sequences:  "[Row #]\tna |@chr[chrom #]:[start]-[end]" + for each sample, "\t[value]" + "\t[average of values]"; where all values are in Arabic numerals and values/averages are decimals
		
3. introns
	reform gene_exons_chromosome*.txt to discover introns and make gene_introns_chromosome*.txt
	format of both files is (gene name, segment number, start, stop, length)
	outputs are generated and unchanging for S. pombe; therefore deprioritize this program
4. segment
	combine (gene_introns_chromosome*.txt or gene_exons_chromosome*.txt) and GCT file to create a new GCT file for each intron/exon's average expression
	for multiple segments that fall within a specific intron/exon, take a length-weighted average for the given intron/exon
	initially, parse GCT file into (chromosome, start, end, value)
	sort & browse through sorted parsed GCT and sorted introns/exons list
	inputs (gene_*_chromosome*.txt):  after first row, "[gene name]\t[segment number]\t[start]\t[stop]\t[length]"
	input (GCT):  starting third row, "[\t]*\t[^|]|@chr[#]:[start]-[end]|.*\t[value or average value]"
	output:
		First row has "#1.2"
		Second row has "[record count]\t[sample count]"
		Third row has "Reporter Identifier\tDescription\t[sample name]"
		Succeeding rows have data, sorted by chr#, then start:  "[Row #]\t[gene name] [segment number] |@chr[chrom #]:[start]-[end]\t[value]"; where all values are in Arabic numerals and values/averages are decimals
