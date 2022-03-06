#!/usr/bin/python3

from lang import *
from ll import *

def get_G():
	return Grammar(
		rules = [
			Rule("S", Word("a", "a", "b")),
			Rule("S", Word("a", "R")),
			Rule("R", Word("a", "b")),
			Rule("R", Word("b", "c", "R")),
			Rule("R", Word("d", "R", "b"))
		]
	)

def test_first():
	G = get_G()
	assert first(0, Word("a", "R"), G) == { Word() }
	assert first(1, Word("a", "R"), G) == { Word("a",) }
	assert first(2, Word("a", "R"), G) == {
		Word('a', 'a'),
		Word('a', 'b'),
		Word('a', 'd')
	}
	assert first(3, Word("a", "R"), G) == {
		Word("a", "a", "b"),
		Word("a", "b", "c"),
		Word("a", "d", "a"),
		Word("a", "d", "b"),
		Word("a", "d", "d")
	}
	assert first(4, Word("a", "R"), G) == {
		Word('a', 'a', 'b'),
		Word('a', 'b', 'c', 'a'),
		Word('a', 'b', 'c', 'b'),
		Word('a', 'b', 'c', 'd'),
		Word('a', 'd', 'a', 'b'),
		Word('a', 'd', 'b', 'c'),
		Word('a', 'd', 'd', 'a'),
		Word('a', 'd', 'd', 'b'),
		Word('a', 'd', 'd', 'd')
	}

def test_follow():
	G = get_G()
	assert follow(0, "S", G) == {Word()}
	assert follow(1, "S'", G) == set()
	assert follow(1, "S", G) == {Word('$',)}
	assert follow(3, "S", G) == {Word('$', '$', '$')}
	assert follow(1, "S", G) == {Word('$',)}
	assert follow(1, "R", G) == {Word('$',), Word('b',)}
	assert follow(2, "R", G) == {
		Word('b', '$'),
		Word('b', 'b'),
		Word('$', '$')
	}

test_first()
test_follow()
#print("Test succeeded!")
