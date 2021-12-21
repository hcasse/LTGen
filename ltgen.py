#!/usr/bin/python3

import argparse
import os.path
import sys

# special values
LL_ACCEPT = -2
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
	if len(w) == 0:
		return u"ε"
	elif type(w) == list:
		return " ".join(w)
	else:
		return " ".join(list(w))

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


# ParseTree class
class ParseTree:
	"""Basic class to represent parse tree and to display it."""

	def __init__(self, sym):
		self.sym = sym
		self.children = []
		self.rule = None

	def get_symbol(self):
		return self.sym

	def get_children(self):
		return self.children

	def append_child(self, child):
		self.children.append(child)

	def prepend_child(self, child):
		self.children.insert(0, child)

	def write_rec(self, out, pref, last):
		out.write(pref)
		out.write(self.sym)
		if self.children == []:
			out.write("\n")
		else:
			out.write(" +\n")
			if last:
				pref = pref[:-2] + "  "
			pref = pref + " "*len(self.sym) + " | "
			for child in self.children:
				child.write_rec(out, pref, child == self.children[-1])

	def write(self, out):
		self.write_rec(out, "", True)

	def __repr__(self):
		return self.sym

	def write_dot(self, out):
		out.write("digraph G {\n")
		out.write("node [ordering=\"out\"];")

		# generate nodes
		todo = [ self ]
		while todo != []:
			n = todo.pop()
			out.write("\"%s\" [label=\"%s\"];\n" % (id(n), n.get_symbol()))
			todo += n.get_children()

		# generates edges
		todo = [ self ]
		while todo != []:
			n = todo.pop()
			if n.rule == None:
				l = -1
			else:
				l = len(n.get_children()) // 2
			i = 0
			for c in n.get_children():
				todo.append(c)
				out.write("\"%s\" -> \"%s\"" % (id(n), id(c)))
				if i == l:
					out.write("[label=\"(%s)\"]" % n.rule)
				out.write(";\n")
				i = i + 1

		out.write("}\n")


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


# LLParser class
class LLParser:
	"""Class to scan a word from the given LL table.
	The scanner takes a word and performs analysis along the call to next.
	Analysis results can be polled from variablmes stack, word and action.
	Action takes the last expanded rule number, the popped terminal or
	special LL_ERROR or LL_ACCEPT."""

	def __init__(self, table, word):
		self.G = table.G
		self.k = table.k
		self.table = table
		self.word = word + ('$',) * self.k
		self.stack = ['$'] * self.k + [self.G.get_top()]
		self.action = 0

	def get_grammar(self):
		return self.G

	def get_k(self):
		return self.k

	def next(self):
		"""Go to the next step."""
		if self.action in { LL_ERROR, LL_ACCEPT }:
			pass
		elif self.stack == []:
			if self.word == ():
				self.action = LL_ACCEPT
			else:
				self.action = LL_ERROR
		elif self.stack[-1] == self.word[0]:
			self.action = self.stack[-1]
			self.stack.pop()
			self.word = self.word[1:]
		else:
			try:
				self.action = self.table.at(self.stack[-1], self.word[:self.k])
				self.stack.pop()
				x = list(self.G.get_rules()[self.action][1])
				x.reverse()
				self.stack += x
			except KeyError:
				self.action = LL_ERROR
	

# LLTable class
class LLTable:
	"""Represents an LL(k) table, that is, indexed by non-terminals
	for rows and terminals for columns. Its content are the rule
	numbers to expand or the special value LL_ERROR."""

	def __init__(self, k, G, las):
		self.k = k
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
		return self.table[self.nt_map[X]][self.la_map[p]]

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
				if c == LL_ERROR:
					out.write("\tERR")
				else:
					out.write("\t(%d)" % c)
			out.write("\n")

	def parse(self, word):
		return LLParser(self, word)


## LLObserver class
class LLObserver:
	"""Base class for LL analysis observer."""

	def on_start(self, parser):
		"""Function called before the analysis startup."""
		pass

	def on_next(self, parser):
		"""Function called at each next step"""
		pass


class LLDisplayObserver(LLObserver):
	"""Observer displaying the LL analysis."""

	def on_start(self, parser):
		self.ps = word_to_str(parser.stack)
		self.pw = word_to_str(parser.word)
		self.size = len(self.pw) + 2
		
		output("{0:{size}} {1:{size}} {2:{size}}" \
			.format("Stack", "Word", "Action", size=self.size))
		output("-"*self.size + " " + "-"*self.size + " " + "-"*12)

	def on_next(self, parser):
		if parser.action == LL_ERROR:
			msg = "error"
		elif parser.action == LL_ACCEPT:
			msg = "accept"
		elif type(parser.action) == int:
			msg = "expand (%d)" % parser.action
		else:
			msg = "pop %s" % word_to_str(parser.action)
		output("{0:{size}} {1:{size}} {2:{size}}" \
			.format(self.ps, self.pw, msg, size=self.size))
		self.ps = word_to_str(parser.stack)
		self.pw = word_to_str(parser.word)


class LLParseTreeObserver(LLObserver):
	"""Observer to build the parse tree."""

	def get_root(self):
		return self.root

	def on_start(self, parser):
		self.root = ParseTree(parser.G.get_top())
		self.stack = [ParseTree("$")] * parser.get_k() + [self.root]
		print(self.stack)

	def on_next(self, parser):
		if type(parser.action) == str:
			self.stack.pop()
		elif parser.action >= 0:
			parent = self.stack[-1]
			parent.rule = parser.action
			self.stack.pop()
			s = parser.get_grammar().get_rules()[parser.action][1]
			for i in range(len(s)-1, -1, -1):
				node = ParseTree(s[i])
				self.stack.append(node)
				parent.prepend_child(node)


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
			f = lookahead(args.k, X, s, G)
		output("%d-lookahead(%s -> %s) = %s" % \
			(args.k, X, word_to_str(s), word_set_to_str(f)))

# print the grammar
if args.print:
	G.print(sys.stdout)

# LL(k) analysis
if args.ll:
	no_action = False

	# perform the analysis
	las = analyze_ll(args.k, G)
	if las == None:
		fatal("%s is not LL(%d)!" % (args.grammar[0], args.k))
	else:
		info("%s is LL(%d)." % (args.grammar[0], args.k))
	table = None

	# generate the table if needed
	if args.table or args.gen_csv == None or args.words != []:
		table = LLTable(args.k, G, las)

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
		observers = [LLDisplayObserver()]
		if args.tree or args.dot:
			tree = LLParseTreeObserver()
			observers.append(tree)
		else:
			tree = None

		# perform the analysis
		w = tuple(w.split())
		parser = table.parse(w)
		for o in observers:
			o.on_start(parser)
		while parser.action not in { LL_ERROR, LL_ACCEPT }:
			parser.next()
			if parser.action == LL_ERROR:
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

