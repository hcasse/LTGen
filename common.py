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

"""Comon resources (like user-interactions)."""

import sys

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

