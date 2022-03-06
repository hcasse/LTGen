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

"""Facilities to manage languages, words, word set, etc."""

from common import *

# formatting functions
#def word_to_str(w):
#	if len(w) == 0:
#		return u"ε"
#	elif type(w) == list:
#		return " ".join(w)
#	else:
#		return " ".join(list(w))

def word_set_to_str(S):
	f = [str(w) for w in S]
	f.sort()
	return "{ %s }" % (", ".join(f))

#def rule_to_str(X, s):
#	return "%s -> %s" % (X, word_to_str(s))

class EmptyWordExcepion(Exception):
	pass


#class UnsupportedOperationExcepion(Exception):
#	pass


# Word class
class Word:
	"""Implements a word and usual operations on a word. A word is made
	of a list of alphabet characters."""

	def __init__(self, *chars):
		self.chars = tuple(chars)

	def is_empty(self):
		return self.chars == ()

	def __len__(self):
		return len(self.chars)

	def prefix(self, k):
		if len(self.chars) <= k:
			return self.chars
		else:
			return self.chars[:k]

	def suffix(self, k):
		if len(self.chars) <= k:
			return self.chars
		else:
			return self.chars[:-k]

	def first(self):
		if self.chars == ():
			raise EmptyWordExcepion
		else:
			return self.chars[0]

	def reverse(self):
		"""Return reverse word from the current word."""
		return Word(*self.chars[::-1])

	def tail(self):
		if self.chars == ():
			raise EmptyWordExcepion
		else:
			return Word(*self.chars[1:])

	def index(self, a, i = 0):
		try:
			return self.chars.index(a, i)
		except ValueError:
			return len(self.chars)

	def __eq__(self, w):
		if not isinstance(w, Word):
			return False
		else:
			return self.chars == w.chars

	def __hash__(self):
		return hash(self.chars)

	def __str__(self):
		if len(self.chars) == 0:
			return u"ε"
		else:
			return " ".join(self.chars)

	def __repr__(self):
		return self.__str__()

	def __iter__(self):
		return iter(self.chars)

	def __getitem__(self, i):
		if type(i) == slice:
			return Word(*self.chars[i])
		else:
			return self.chars[i]

	def __add__(self, w):
		if type(w) == Word:
			return Word(*self.chars, *w.chars)
		elif type(w) == str:
			return Word(*self.chars, w)
		else:
			raise NotImplemented()

	def __radd__(self, w):
		if type(w) == Word:
			return Word(*w.chars, *self.chars)
		elif type(w) == str:
			return Word(w, *self.chars)
		else:
			raise NotImplemented()

	def __mul__(self, k):
		if type(k) != int:
			raise NotImplemented()
		else:
			return Word(*(self.chars * k))

EMPTY_WORD = Word()


# Rule class
class Rule:
	"""Represents a rule: X -> w."""

	def __init__(self, X, w):
		self.X = X
		if type(w) == Word:
			self.w = w
		else:
			self.w = Word(*w)

	def __str__(self):
		return "%s -> %s" % (self.X, self.w)
		

# Grammar class
class Grammar:
	"""Class representing a grammar. It is defined its axiom and its
	list of rules. Any symbol not defined by a rule is considered
	as a token (terminal)."""

	def __init__(self, rules = None, text = None):
		if text != None:
			self.parse_text(rules, text)
		elif type(rules) == str:
			self.parse_file(rules)
		else:
			self.rules = rules
		self.tokens = set()
		self.names = set()
		for rule in self.rules:
			for a in rule.w:
				self.tokens.add(a)
		for rule in self.rules:
			self.names.add(rule.X)
		self.top = "S'"
		while self.top in self.tokens:
			self.top = self.top + "'"
		self.rules = [Rule(self.top, (self.rules[0].X,))] + self.rules
		self.tokens = list(self.tokens - self.names)
		self.names = [self.top] + list(self.names)

	def get_top(self):
		return self.top

	def is_token(self, id):
		return id in self.tokens

	def rules_for(self, id):
		return [r.w for r in self.rules if r.X == id]

	def get_rules(self):
		return self.rules

	def print(self, out):
		n = 0
		for rule in self.rules:
			out.write("(%d) %s\n" % (n, rule))
			n = n + 1

	def parse(self, path, lines):
		n = 0
		self.rules = []
		for l in lines:
			n = n + 1
			if l == "":
				continue
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
				if len(aa) == 1:
					hd = aa[0]
				elif len(aa) == 0 and len(self.rules) != 0:
					hd = self.rules[-1][0]
				else:
					error("%s:%d: malformed rule." % (path, n))
					hd = None
				if hd != None:
					s = l[i+2:].split()
					self.rules.append(Rule(hd, Word(*s)))
			except ValueError:
				error("%s:%d: malformed line:\n%s\n" % (path, n, l))
		if self.rules == []:
			fatal("empty grammar in %s" % path)

	def parse_text(self, path, text):
		self.parse(path, text.split("\n"))

	def parse_file(self, path):
		self.parse(path, open(path))


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
	#print("DEBUG: first(", k, ", ", s, ", ", g)
	if k == 0 or len(s) == 0:
		r = { EMPTY_WORD }
	elif g.is_token(s[0]):
		r = {s.first() + p for p in first(k-1, s.tail(), g)}
	else:
		r = {w for ss in g.rules_for(s[0])
				if ss == [] or ss[0] != s[0]
					for w in first(k, ss + s[1:], g)}
	return r


def firstfollow(k, X, s, G, L):
	#print("call firstfollow%d(%s, %s)" % (k, X, s))
	P = first(k, s, G)
	m = max([k - len(p) for p in P])
	if m == 0:
		r = P
	else:
		F = rec_follow(m, X, G, L)
		r = {(p + f)[:k] for f in F for p in P}
	#print("return firstfollow%d(%s, %s) = %s" % (k, X, s, r))
	return r


def rec_follow(k, X, G, L = set()):
	"""Compute followk(X) in grammar G in a recursive way.
	L is the link list of recursive follow to avoid endless linkage."""
	#print("DEBUG: call rec_follow%d(%s)" % (k, X))
	L = L | { X }
	if k == 0:
		r = { EMPTY_WORD }
	else:
		r = set()
		for rule in G.get_rules():

			# axiom case
			if rule.X == G.top and X == rule.w[0]:
				r |= { Word("$") * k }
				continue

			# get all prefixes following X
			i = 0
			ir = set()
			while i < len(rule.w):
				i = rule.w.index(X, i)
				if i < len(rule.w):
					i = i + 1
					w = rule.w[i:]
					if len(w) != 0 or rule.X not in L:
						r |= firstfollow(k, rule.X, w, G, L)

	#print("DEBUG: return rec_follow%d(%s) = %s" % (k, X, r))
	return r

def follow(k, X, G):
	"""Compute follow_k(X)."""
	return rec_follow(k, X, G)
