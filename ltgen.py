#!/usr/bin/python3
#
#	Language Theory GENerator
#	Copyright (C) 2021  Hugues Cassé <hug.casse@gmail.com>
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import argparse
import os.path
import sys

from common import *
from lang import *
import ll


# main command
parser = argparse.ArgumentParser(
	description=
"""
Language Theory GENerator
Copyright (c) 2021 - H. Cassé <hug.casse@gmail.com>
"""
)
parser.add_argument('grammar', type=str, nargs=1,
	help="Grammar to use.")
parser.add_argument('names', type=str, nargs='*',
	help="List of all non-terminals to work on.")
parser.add_argument('--k', type=int, default=1,
	help="Specify the analysis depth (default to 1).")
parser.add_argument("--first", action="store_true",
	help="Compute the firsts.")
parser.add_argument("--follow", action="store_true",
	help="Compute the follows.")
parser.add_argument("--lookahead", action="store_true",
	help="Compute the lookahead.")
parser.add_argument("--ll", action="store_true",
	help="Perform LL(k) analysis.")
parser.add_argument("--gen-csv", action="store_true",
	help="Generate the analysis table in CSV format.")
parser.add_argument("--print", action="store_true",
	help="Print the grammar.")
parser.add_argument("--output", "-o", type=str, nargs="?", default=None,  const="",
	help="Generate the analysis table in CSV format.")
parser.add_argument("--table", action="store_true",
	help="Generate the table for the used analysis.")
parser.add_argument("--words", "-w", type=str, nargs="*", default=[],
	help="Parse the given word after the analysis.")
parser.add_argument("--tree", action="store_true",
	help="Display the parse tree.")
parser.add_argument("--dot", action="store_true",
	help="Display the parse tree as .dot format.")


# get the grammar
args = parser.parse_args()
G = Grammar(args.grammar[0])

# prepare the arguments
no_action = True
if args.names != []:
	names = args.names
else:
	names = G.names
exit_code = 0

# msic. calculations
if args.first:
	no_action = False
	for n in names:
		f = first(args.k, (n, ), G)
		output("first%d(%s) = %s" % (args.k, n, word_set_to_str(f)))
if args.follow:
	no_action = False
	for n in names:
		f = follow(args.k, n, G)
		output("follow%d(%s) = %s" % (args.k, n, word_set_to_str(f)))
if args.lookahead:
	no_action = False
	for (X, s) in G.get_rules():
		if X in names:
			f = ll.lookahead(args.k, X, s, G)
		output("%d-lookahead(%s -> %s) = %s" % \
			(args.k, X, word_to_str(s), word_set_to_str(f)))

# print the grammar
if args.print:
	G.print(sys.stdout)

# LL(k) analysis
if args.ll:
	no_action = False

	# perform the analysis
	las = ll.analyze(args.k, G)
	if las == None:
		fatal("%s is not LL(%d)!" % (args.grammar[0], args.k))
	else:
		info("%s is LL(%d)." % (args.grammar[0], args.k))
	table = None

	# generate the table if needed
	if args.table or args.gen_csv == None or args.words != []:
		table = ll.Table(args.k, G, las)

	# output the results
	if args.table or args.gen_csv == None:
		if args.output != None:
			if args.output != "":
				path = args.output
			else:
				if args.gen_csv:
					ext = ".csv"
				else:
					ext = ".txt"
				path = os.path.splitext(args.grammar[0])[0] + ext
			out = open(path, "w")
		else:
			out = sys.stdout
		if args.gen_csv:
			table.write_to_csv(out)
		else:
			table.write(out)
		if out != sys.stdout:
			out.close()

	# word analysis
	for w in args.words:

		# prepare observers
		observers = [ll.DisplayObserver()]
		if args.tree or args.dot:
			tree = ll.ParseTreeObserver()
			observers.append(tree)
		else:
			tree = None

		# perform the analysis
		w = tuple(w.split())
		parser = table.parse(w)
		for o in observers:
			o.on_start(parser)
		while not parser.is_ended():
			parser.next()
			if parser.action == ll.ERROR:
				exit_code = 2
			for o in observers:
				o.on_next(parser)

		# postprocess the observers
		if tree != None or args.dot:
			if args.output == None:
				out = sys.stdout
			else:
				if args.output != "":
					path = args.output
				else:
					if args.dot:
						ext = ".dot"
					else:
						ext = ".txt"
					path = word_to_str(w) + ext
				out = open(path, "w")
			if args.dot:
				tree.get_root().write_dot(out)
			else:
				tree.get_root().write(out)
			if out != sys.stdout:
				out.close()

if no_action:
	G.print(sys.stdout)

# exit
sys.exit(exit_code)

