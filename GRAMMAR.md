# Onyx Part 5 – Complete Grammar (Functions, Scope, and Arrays)

```ebnf
<program> ::= { <statement> }

<statement> ::= <assignment>
              | <print-statement>
              | <if-statement>
              | <while-statement>
              | <function-definition>
              | <return-statement>
              | <function-call> ";"

<assignment> ::= "let" <identifier> "=" <expression> ";"
               | <identifier> "=" <expression> ";"
               | <identifier> "[" <expression> "]" "=" <expression> ";"

<print-statement> ::= "print" "(" <expression> ")" ";"

<if-statement> ::= "if" "(" <expression> ")" "{" <program> "}"
                   [ "else" "{" <program> "}" ]

<while-statement> ::= "while" "(" <expression> ")" "{" <program> "}"

<function-definition> ::= "def" <identifier> "(" [ <parameter-list> ] ")" "{" <program> "}"

<return-statement> ::= "return" <expression> ";"

<expression> ::= <comparison-expr>

<comparison-expr> ::= <arithmetic-expr> [ <comparison-operator> <arithmetic-expr> ]

<arithmetic-expr> ::= <term> { ("+" | "-") <term> }

<term> ::= <factor> { ("*" | "/") <factor> }

<factor> ::= <number>
           | <identifier>
           | <function-call>
           | <array>
           | <identifier> "[" <expression> "]"
           | "(" <expression> ")"

<function-call> ::= <identifier> "(" [ <argument-list> ] ")"

<parameter-list> ::= <identifier> { "," <identifier> }

<argument-list> ::= <expression> { "," <expression> }

<array> ::= "[" [ <argument-list> ] "]"

<comparison-operator> ::= "==" | "!=" | "<" | ">" | "<=" | ">="

<identifier> ::= [a-zA-Z_] { [a-zA-Z0-9_] }

<number> ::= [0-9] { [0-9] }
