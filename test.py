#!/usr/bin/python3

from ltgen import *

def get_G():
	return Grammar(
		"S'",
		[
			("S'", ("S")),
			("S", ("a", "a", "b")),
			("S", ("a", "R")),
			("R", ("a", "b")),
			("R", ("b", "c", "R")),
			("R", ("d", "R", "b"))
		]
	)

def test_first():
	G = get_G()
	assert first(0, ("a", "R"), G) == { () }
	assert first(1, ("a", "R"), G) == { ("a",) }
	assert first(2, ("a", "R"), G) == { ('a', 'a'), ('a', 'b'), ('a', 'd') }
	assert first(3, ("a", "R"), G) == {
		("a", "a", "b"),
		("a", "b", "c"),
		("a", "d", "a"),
		("a", "d", "b"),
		("a", "d", "d")
	}
	assert first(4, ("a", "R"), G) == {
		('a', 'a', 'b'),
		('a', 'b', 'c', 'a'),
		('a', 'b', 'c', 'b'),
		('a', 'b', 'c', 'd'),
		('a', 'd', 'a', 'b'),
		('a', 'd', 'b', 'c'),
		('a', 'd', 'd', 'a'),
		('a', 'd', 'd', 'b'),
		('a', 'd', 'd', 'd')
	}

def test_follow():
	G = get_G()
	assert follow(0, "S", G) == {()}
	assert follow(1, "S'", G) == {('$',)}
	assert follow(3, "S'", G) == {('$', '$', '$')}
	assert follow(1, "S", G) == {('$',)}
	assert follow(1, "R", G) == {('$',), ('b',)}
	assert follow(2, "R", G) == {('b', '$'), ('b', 'b'), ('$', '$')}

G = get_G()
