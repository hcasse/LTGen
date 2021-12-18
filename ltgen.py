#!/usr/bin/python3

class Grammar:

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


def first(k, s, g):
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
	return rec_follow(k, X, G, set())


def lookahead(k, r, g):
	pass


