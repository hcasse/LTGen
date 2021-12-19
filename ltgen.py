#!/usr/bin/python3

import argparse
import os.path
import sys

# special values
LL_ERROR = -1


# IO functions
def error(msg):
	"""Display an error."""
	sys.stderr.write("ERROR: %s\n" % msg)

def fatal(msg):
	"""Display an error and stop the execution."""
	error(msg)
	sys.exit(1)

def info(msg):
	"""Display an information to the user (but this information is not
	part of the result)."""
	sys.stderr.write("%s\n" % msg)

def output(msg):
	"""Display a result to the user."""
	sys.stdout.write("%s\n" % msg)


# formatting functions
def word_to_str(w):
	return " ".join(w)

def word_set_to_str(S):
	f = [word_to_str(w) for w in S]
	f.sort()
	return "{ %s }" % (", ".join(list(f)))

def rule_to_str(X, s):
	return "%s -> %s" % (X, word_to_str(s))


# Grammar class
class Grammar:
	"""Class representing a grammar. It is defined its axiom and its
	list of rules. Any symbol not defined by a rule is considered
	as a token (terminal)."""

	def __init__(self, rules):
		if type(rules) == str:
			self.parse(rules)
		else:
			self.rules = rules
		self.tokens = set()
		self.names = set()
		for (_, s) in self.rules:
			for a in s:
				self.tokens.add(a)
		for (X, _) in self.rules:
			self.names.add(X)
		self.top = "S'"
		while self.top in self.tokens:
			self.stop = self.top + "'"
		self.rules = [(self.top, (self.rules[0][0],))] + self.rules
		self.tokens = list(self.tokens - self.names)
		self.names = [self.top] + list(self.names)

	def get_top(self):
		return self.top

	def is_token(self, id):
		return id in self.tokens

	def rules_for(self, id):
		return [s for (i, s) in self.rules if i == id]

	def get_rules(self):
		return self.rules

	def print(self, out):
		n = 0
		for (X, s) in self.rules:
			out.write("(%d) %s\n" % (n, rule_to_str(X, s)))
			n = n + 1

	def parse(self, path):
		n = 0
		self.rules = []
		for l in open(path):
			n = n + 1
			if l[-1] == "\n":
				l = l[:-1]
			if "#" in l:
				l = l[:l.index("#")]
			l = l.strip()
			if l == "":
				continue
			try:
				i = l.index("->")
				aa = l[:i].split()
				if len(aa) != 1:
					error("%s:%d: malformed rule." % (path, n))
				s = l[i+2:].split()
				self.rules.append((aa[0], tuple(s)))
			except ValueError:
				error("%s:%d: malformed line:\n%s\n" % (path, n, l))
		if self.rules == []:
			fatal("empty grammar in %s" % path)


# Language computation
def first(k, s, g):
	"""Compute first_k(s)."""
	if k == 0 or len(s) == 0:
		r = {()}
	elif g.is_token(s[0]):
		r = {s[0:1] + p for p in first(k-1, s[1:], g)}
	else:
		r = {p for ss in g.rules_for(s[0]) for p in first(k, ss + s[1:], g)}
	#print("first%d(%s) = %s" % (k, s, r))
	return r


def firstfollow(k, X, s, G):
	#print("call firstfollow%d(%s, %s)" % (k, X, s))
	P = first(k, s, G)
	m = max([k - len(p) for p in P])
	if m == 0:
		r = P
	else:
		F = follow(m, X, G)
		r = {(p + f)[:k] for f in F for p in P}
	#print("return firstfollow%d(%s, %s) = %s" % (k, X, s, r))
	return r


def rec_follow(k, X, G, L):
	#print("call rec_follow%d(%s, %s)" % (k, X, L))
	if X in L:
		r = set()
	elif k == 0:
		r = {()}
	elif X == G.get_top():
		r = {("$",) * k}
	else:
		r = set()
		for (Y, s) in G.get_rules():
			try:
				i = 0
				while True:
					i = s.index(X, i)
					if i == len(s)-1:
						r |= rec_follow(k, Y, G, L | {X})
					else:
						r |= firstfollow(k, Y, s[i+1:], G)
					i = i + 1
			except ValueError:
				pass
	#print("return rec_follow%d(%s, %s) = %s" % (k, X, L, r))
	return r
	


def follow(k, X, G):
	"""Compute follow_k(X)."""
	return rec_follow(k, X, G, set())


def lookahead(k, X, s, G):
	return firstfollow(k, X, s, G)


def analyze_ll(k, G):
	"""Perform a LL(k) analysis on the given grammar. If successful,
	returns the lookaheads as a list of (rule number, non-terminal,
	symbol sequence, look-ahead words)."""
	total_success = True
	las = []
	for X in G.names:

		# compute lookahead
		rs = []
		n = 0
		for (Y, s) in G.get_rules():
			if X == Y:
				rs.append((n, X, s, lookahead(k, X, s, G)))
			n = n + 1
		las += rs

		# check if the intersection is empty
		success = True
		for i in range(0, len(rs)):
			for j in range(i+1, len(rs)):
				I = rs[i][3] & rs[j][3]
				if I != set():
					if success:
						success = False
						for (n, X, s, l) in rs:
							print("(%d) %d-lookahead(%s -> %s) = %s" \
								%(n, k, X, word_to_str(s), word_set_to_str(l)))
					print("I%d conflicts with I%d: %s" \
						% (rs[i][0], rs[j][0], word_set_to_str(I)))

		total_success &= success

	if total_success:
		return las
	else:
		return None


# LLTable class
class LLTable:
	"""Represents an LL(k) table, that is, indexed by non-terminals
	for rows and terminals for columns. Its content are the rule
	numbers to expand or the special value LL_ERROR."""

	def __init__(self, G, las):
		self.G = G

		# non-terminals
		self.nts = list(G.names)
		self.nt_map = {}
		for i in range(0, len(self.nts)):
			self.nt_map[self.nts[i]] = i

		# lookaheads
		self.las = set()
		for (n, X, s, la) in las:
			for w in la:
				self.las |= { w }
		self.las = list(self.las)
		self.la_map = {}
		for i in range(0, len(self.las)):
			self.la_map[self.las[i]] = i

		# prepare the table
		self.table = []
		for i in range(0, len(self.nts)):
			self.table.append([LL_ERROR] * len(self.las))

		# set the table
		for (n, X, s, la) in las:
			for w in la:
				self.table[self.nt_map[X]][self.la_map[w]] = n

	def at(self, X, p):
		"""Give the table value for non-terminal X and terminal a.
		This value is the rule to expand or None for an error."""
		x = self.table[self.nt_map[X]][self.la_map[p]]
		if x == LL_ERR:
			return None
		else:
			return self.G.get_rules()[x][1]

	def get_non_terminals(self):
		return self.nts

	def get_lookaheads(self):
		return self.las

	def write_to_csv(self, out):
		"""Write the given table to a CSV flow."""
		for la in self.las:
			out.write(",%s" % word_to_str(la))
		out.write("\n")
		for X in self.nts:
			out.write(X)
			for c in self.table[self.nt_map[X]]:
				out.write(",%d" % c)
			out.write("\n")

	def write(self, out):
		"""Write the table in human readable way."""
		for la in self.las:
			out.write("\t%s" % word_to_str(la))
		out.write("\n")
		for X in self.nts:
			out.write(X)
			for c in self.table[self.nt_map[X]]:
				out.write("\t%d" % c)
			out.write("\n")


# main command
parser = argparse.ArgumentParser(description='Language Theory GENerator')
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
parser.add_argument("--output", "-o", type=str, nargs="?", default=None,  const="",
	help="Generate the analysis table in CSV format.")
parser.add_argument("--table", action="store_true",
	help="Generate the table for the used analysis.")



# get the grammar
args = parser.parse_args()
G = Grammar(args.grammar[0])


# prepare the arguments
no_action = True
if args.names != []:
	names = args.names
else:
	names = G.names


# perform the action
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
			f = lookahead(args.k, X, s, G)
		output("%d-lookahead(%s -> %s) = %s" % \
			(args.k, X, word_to_str(s), word_set_to_str(f)))
if args.ll:
	no_action = False
	las = analyze_ll(args.k, G)
	if las == None:
		fatal("%s is not LL(%d)!" % (args.grammar[0], args.k))
	else:
		info("%s is LL(%d)." % (args.grammar[0], args.k))
	if args.table or args.gen_csv == None:
		table = LLTable(G, las)
		print(args)
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

if no_action:
	G.output(sys.stdout)
