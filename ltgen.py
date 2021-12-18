#!/usr/bin/python3

import argparse
import sys

def error(msg):
	sys.stderr.write("ERROR: %s\n" % msg)


def fatal(msg):
	error(msg)
	sys.exit(1)



def word_to_str(w):
	return " ".join(w)


def word_set_to_str(S):
	f = [word_to_str(w) for w in S]
	f.sort()
	return "{ %s }" % (", ".join(list(f)))


def rule_to_str(X, s):
	return "%s -> %s" % (X, word_to_str(s))


class Grammar:
	"""Class representing a grammar. It is defined its axiom and its
	list of rules. Any symbol not defined by a rule is considered
	as a token (terminal)."""

	def __init__(self, top, rules):
		self.top = top
		self.rules = rules
		self.tokens = set()
		self.names = set()
		for (_, s) in rules:
			for a in s:
				self.tokens.add(a)
		for (X, _) in rules:
			self.names.add(X)
		self.tokens = self.tokens - self.names

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
	total_success = True
	for X in G.names:

		# compute lookahead
		rs = []
		n = 0
		for (Y, s) in G.get_rules():
			if X == Y:
				rs.append((n, s, lookahead(k, X, s, G)))
			n = n + 1

		# check if the intersection is empty
		success = True
		for i in range(0, len(rs)):
			for j in range(i+1, len(rs)):
				I = rs[i][2] & rs[j][2]
				if I != set():
					if success:
						success = False
						for (n, s, l) in rs:
							print("(%d) %d-lookahead(%s -> %s) = %s" \
								%(n, k, X, word_to_str(s), word_set_to_str(l)))
					print("I%d conflicts with I%d: %s" \
						% (rs[i][0], rs[j][0], word_set_to_str(I)))

		total_success &= success

	return total_success
		

def parse(path):
	"""Parse the given file and, if there is no error, return the
	corresponding grammar."""
	n = 0
	a = None
	rs = []
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
			if a == None:
				a = aa[0]
			s = l[i+2:].split()
			rs.append((aa[0], tuple(s)))
		except ValueError:
			error("%s:%d: malformed line:\n%s\n" % (path, n, l))
	if a == None:
		fatal("empty grammar in %s" % path)
	else:
		return Grammar(a, rs)


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


# get the grammar
args = parser.parse_args()
G = parse(args.grammar[0])


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
		print("first%d(%s) = %s" % (args.k, n, word_set_to_str(f)))
if args.follow:
	no_action = False
	for n in names:
		f = follow(args.k, n, G)
		print("follow%d(%s) = %s" % (args.k, n, word_set_to_str(f)))
if args.lookahead:
	no_action = False
	for (X, s) in G.get_rules():
		if X in names:
			f = lookahead(args.k, X, s, G)
		print("%d-lookahead(%s -> %s) = %s" % \
			(args.k, X, word_to_str(s), word_set_to_str(f)))
if args.ll:
	no_action = False
	analyze_ll(args.k, G)

if no_action:
	G.print(sys.stdout)
