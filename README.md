# LTGen

**LTGen** stands for *Language Theory GENerator* and provides tools
to implement language theory.

## `.gram` Files

Grammar can be expressed using `.gram`files. The format is very simple:
  * Rules are organized by lines.
  * A rule has the format: *NAME* `->` *SYM1* *SYM2* ...
  * A symbol or a rule name can be any sequence of character that do contain spaces or tabulations.
  * The name of the first rule is the axiom of the grammar.
  * Empty lines are accepted.
  * Comments spans from the `#` to the end of the line. 

## Testing

Unit is performed using `pytest` with the command:

	$ pytest test.py
	

