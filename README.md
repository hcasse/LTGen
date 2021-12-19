# LTGen

**LTGen** stands for *Language Theory GENerator* and provides tools
to implement language theory.

## Command Line

**LTGen** is a collection of tools to implement basic algorithms used in *Language Theory*. The command line arguments are mostly the same for the provided tools:

	$ ltgen.py GRAMMAR OPTIONS? NON-TERMINALS?

Where *GRAMMAR* is path to a file containing the grammar to work with
(format is detailed below).

*OPTIONS* are detailed in the following sections but some (provided below)
are shared by all tools:
  * `--k` -- select the lookup depth used in the tools.
  * `--table` -- output the analysis table (if any).
  * `--gen-csv` -- output the analysis table in CSV (if any).
  * `--output|-o` *PATH*? -- output to the analysis table to a file (with the given *PATH* or to path derived from the grammar file).
  * `--word|-w` "*WORD*" -- scan the *WORD* with the current analysis (separate non-terminals in the word by spaces).
  * `--print` -- print the current grammar (useful un conjunction with `--word)`.
  * `--table` -- print the analysis table.

If no options is given, the used grammar is just displayed.

*NON-TERMINALS* are the names of non-terminal in the *GRAMMAR* to work with. The performed work depends on the selected type of analysis (see below).


## LL(k) Analysis

**LTgen** provides basics for [LL(k)](https://en.wikipedia.org/wiki/LL_parser) analysis:
  * `--first` -- computes *first_k(X)* for all or for listed non-terminals,
  * `--follow` -- computes *follow_(k)* for all or for listed non-terminals,
  * `--lookahead` -- computes *k-lookahead(X -> s)* for all or for listed nion-terminal productions.
  * `--ll` -- Test if the given grammar is *LL(k)*.


## `.gram` Files

Grammar can be expressed using `.gram`files. The format is very simple:
  * Rules are organized by lines.
  * A rule has the format: *NAME* `->` *SYM1* *SYM2* ...
  * A symbol or a rule name can be any sequence of character that do contain spaces or tabulations.
  * The name of the first rule is the axiom of the grammar.
  * Empty lines are accepted.
  * Comments spans from the `#` to the end of the line. 
  * Notice that the symbol `$` is reserved to mark the end of word.

**Example of grammar:**

	S'	->	S
	S	->	a S b
	S	->	R
	R	->	b
	R	->	c R


## Testing

Unit is performed using `pytest` with the command:

	$ pytest test.py
	

