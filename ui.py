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

# My own page
class MyPage(Page):

	def __init__(self):
		common.STDOUT = self
		common.STDERR = self
		common.EXIT = self.exit
		llk = Button("LL(k)")
		first = Button("first(k)", on_click = self.on_first)
		follow = Button("follow(k)")
		lookahead = Button("lookahead(k)")
		self.grammar = Editor()
		self.console = Console(init = "Welcome to LTGen!\n\n")
		self.k = Field("k = ", 1, 3, is_valid = is_valid_number) 
		Page.__init__(self,
			VGroup(
				HGroup(
					llk,
					first,
					follow,
					lookahead,
					self.k
				),
				HGroup(
					VGroup(
						Label("<b>Grammar</b>"),
						self.grammar
					),
					VGroup(
						Label("<b>Console</b>"),
						self.console
					)
				)
			),
			template = "assets/template.html"
		)
		EnableIf(IsValid(self.k), llk, first, follow, lookahead)

	def on_first(self):
		self.grammar.get_content(self.do_first)

	def do_first(self, grammar, content):
		G = lang.Grammar("G", content)
		k = int(self.k.get_content())
		for n in G.names:
			f = lang.first(k, (n, ), G)
			self.console.append("first%d(%s) = %s" % (k, n, lang.word_set_to_str(f)))
		self.console.append("")

	def write(self, msg):
		self.console.append(msg[:-1])

	def exit(self, n):
		pass


def run(port):
	orchid.run(MyPage, port = port)
