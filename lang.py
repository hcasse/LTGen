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

	def __init__(self, rules = None, text = None):
		if text != None:
			self.parse_text(rules, text)
		elif type(rules) == str:
			self.parse_file(rules)
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
				if len(aa) != 1:
					error("%s:%d: malformed rule." % (path, n))
				else:
					s = l[i+2:].split()
					self.rules.append((aa[0], tuple(s)))
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
	if k == 0 or len(s) == 0:
		r = {()}
	elif g.is_token(s[0]):
		r = {s[0:1] + p for p in first(k-1, s[1:], g)}
	else:
		r = {p for ss in g.rules_for(s[0])
				if ss == [] or ss[0] != s[0]
					for p in first(k, ss + s[1:], g)}
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
