Operator Precedence
===================

Operator/Element | Associativity | Description
---------------- | ------------- | --------------
`-`              | right         | unary minus
`^`              | left          | exponentiation
`*` `/` `%`      | left          | multiplication, division, modulo
`+` `-`          | left          | addition, subtraction
`IS`             |               | test for `true`, `false`, `null`
`IN`             |               | set membership

BETWEEN         containment
OVERLAPS         time interval overlap
LIKE ILIKE         string pattern matching
< >         less than, greater than
=    right    equality, assignment
NOT    right    logical negation
AND    left    logical conjunction
OR    left    logical disjunction