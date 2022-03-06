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

"""LL(k) parser generator and analyzer."""

from common import *
from lang import *

# special values
ACCEPT = -2
ERROR = -1

# Analysis
def lookahead(k, X, s, G):
	return firstfollow(k, X, s, G, {X})


def analyze(k, G):
	"""Perform a LL(k) analysis on the given grammar. If successful,
	returns the lookaheads as a list of (rule number, non-terminal,
	symbol sequence, look-ahead words)."""
	total_success = True
	las = []
	for X in G.names:

		# compute lookahead
		rs = []
		n = 0
		for rule in G.get_rules():
			if X == rule.X:
				rs.append((n, X, rule.w, lookahead(k, X, rule.w, G)))
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
								%(n, k, X, s, word_set_to_str(l)))
					print("I%d conflicts with I%d: %s" \
						% (rs[i][0], rs[j][0], word_set_to_str(I)))

		total_success &= success

	if total_success:
		return las
	else:
		return None


# Parser class
class Parser:
	"""Class to scan a word from the given LL table.
	The scanner takes a word and performs analysis along the call to next.
	Analysis results can be polled from variablmes stack, word and action.
	Action takes the last expanded rule number, the popped terminal or
	special ERROR or ACCEPT."""

	def __init__(self, table, word):
		self.G = table.G
		self.k = table.k
		self.table = table
		self.word = word + Word('$') * self.k
		self.stack = Word(*('$' * self.k), self.G.get_top())
		self.action = 0

	def get_grammar(self):
		return self.G

	def get_k(self):
		return self.k

	def is_ended(self):
		return self.action in { ERROR, ACCEPT }

	def next(self):
		"""Go to the next step."""
		if self.is_ended():
			pass
		elif self.stack.is_empty():
			if self.word.is_empty():
				self.action = ACCEPT
			else:
				self.action = ERROR
		elif self.stack[-1] == self.word[0]:
			self.action = self.stack[-1]
			self.stack = self.stack[:-1]
			self.word = self.word[1:]
		else:
			try:
				self.action = self.table.at(self.stack[-1], self.word[:self.k])
				self.stack = self.stack[0:-1]
				x = self.G.get_rules()[self.action].w.reverse()
				self.stack += x
			except KeyError:
				self.action = ERROR
	

# Table class
class Table:
	"""Represents an LL(k) table, that is, indexed by non-terminals
	for rows and terminals for columns. Its content are the rule
	numbers to expand or the special value ERROR."""

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
			self.table.append([ERROR] * len(self.las))

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
			out.write(",%s" % la)
		out.write("\n")
		for X in self.nts:
			out.write(X)
			for c in self.table[self.nt_map[X]]:
				out.write(",%d" % c)
			out.write("\n")

	def write(self, out):
		"""Write the table in human readable way."""
		for la in self.las:
			out.write("\t%s" % la)
		out.write("\n")
		for X in self.nts:
			out.write(X)
			for c in self.table[self.nt_map[X]]:
				if c == ERROR:
					out.write("\tERR")
				else:
					out.write("\t(%d)" % c)
			out.write("\n")

	def parse(self, word):
		return Parser(self, word)


## Observer class
class Observer:
	"""Base class for LL analysis observer."""

	def on_start(self, parser):
		"""Function called before the analysis startup."""
		pass

	def on_next(self, parser):
		"""Function called at each next step"""
		pass


class DisplayObserver(Observer):
	"""Observer displaying the LL analysis."""

	def on_start(self, parser):
		self.ps = parser.stack
		self.pw = parser.word
		self.size = len(self.pw) * 2 - 1
		
		output("{0:{size}} {1:{size}} {2:{size}}" \
			.format("Stack", "Word", "Action", size=self.size))
		output("-"*self.size + " " + "-"*self.size + " " + "-"*12)

	def on_next(self, parser):
		if parser.action == ERROR:
			msg = "error"
		elif parser.action == ACCEPT:
			msg = "accept"
		elif type(parser.action) == int:
			msg = "expand (%d)" % parser.action
		else:
			msg = "pop %s" % parser.action
		output("{0:{size}} {1:{size}} {2:{size}}" \
			.format(str(self.ps), str(self.pw), msg, size=self.size))
		self.ps = parser.stack
		self.pw = parser.word


class ParseTreeObserver(Observer):
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


