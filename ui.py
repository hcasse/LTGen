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

"""Provides a user-interface as an HTTP server."""

import orchid
from orchid import *
import common
import lang
import ll
from functools import partial

# FatalException class
class FatalException(BaseException):
	pass

# My own page
class MyPage(Page):

	def __init__(self):
		common.STDOUT = self
		common.STDERR = self
		common.EXIT = self.exit
		llk = Button("LL(k)",
			on_click = partial(self.get_grammar, self.do_ll_check))
		first = Button("first(k)",
			on_click = partial(self.get_grammar, self.do_first))
		follow = Button("follow(k)",
			on_click = partial(self.get_grammar, self.do_follow))
		lookahead = Button("lookahead(k)",
			on_click = partial(self.get_grammar, self.do_lookahead))
		self.grammar = Editor()
		self.console = Console(init = "Welcome to LTGen!\n\n")
		self.k = Field("k = ", 1, 3, is_valid = is_valid_number) 
		Page.__init__(self,
			VGroup([
				HGroup([
					llk,
					first,
					follow,
					lookahead,
					self.k
				]),
				HGroup([
					VGroup([
						Header("Grammar"),
						self.grammar
					]),
					VGroup([
						Header("Console", [
							ToolButton(Icon("eraser-fill"), on_click=self.clear_console)
						]),
						self.console
					])
				])
			]),
			template = "assets/template.html"
		)
		EnableIf(IsValid(self.k), llk, first, follow, lookahead)

	def get_grammar(self, f):
		self.grammar.get_content(partial(self.parse, f))

	def parse(self, f, grammar, content):
		try:
			G = lang.Grammar("G", content)
			k = int(self.k.get_content())
			print("DEBUG: k=", k)
			f(G, k)
		except FatalException:
			self.console.append("Stopped")
		

	def do_first(self, G, k):
		for n in G.names:
			f = lang.first(k, (n, ), G)
			self.console.append("first%d(%s) = %s" % (k, n, lang.word_set_to_str(f)))
		self.console.append("")

	def do_follow(self, G, k):
		for n in G.names:
			f = lang.follow(k, n, G)
			self.console.append("follow%d(%s) = %s" % (k, n, lang.word_set_to_str(f)))
		self.console.append("")

	def do_lookahead(self, G, k):
		for (X, s) in G.get_rules():
			f = ll.lookahead(k, X, s, G)
			self.console.append("%d-lookahead(%s -> %s) = %s" % \
				(k, X, lang.word_to_str(s), lang.word_set_to_str(f)))
		self.console.append("")

	def do_ll_check(self, G, k):
		las = ll.analyze(k, G)
		if las == None:
			common.fatal("G is not LL(%d)!" % k)
		else:
			common.info("G is LL(%d)." % k)
		self.console.append("")

	def write(self, msg):
		self.console.append(msg[:-1])

	def exit(self, n):
		raise FatalException()

	def clear_console(self):
		self.console.clear()


def run(port):
	orchid.run(MyPage, port = port, dirs = ["./assets"])
