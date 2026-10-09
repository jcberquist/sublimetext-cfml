// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    // A statement without a semicolon continues on the next line only when
    // that line starts with a binary operator. Each first line ends in a
    // literal: after a variable the next line is read as an operator anyway.
    function continued() {
        r = true
            and two;
//          ^^^ keyword.operator.logical.cfml
//              ^^^ variable.other.readwrite.cfml
        r = true
            AND two;
//          ^^^ keyword.operator.logical.cfml
//              ^^^ variable.other.readwrite.cfml
        r = true
            Or two;
//          ^^ keyword.operator.logical.cfml
        r = true
            XOR two;
//          ^^^ keyword.operator.logical.cfml
        r = true
            eqv two;
//          ^^^ keyword.operator.logical.cfml
        r = true
            Imp two;
//          ^^^ keyword.operator.logical.cfml
        r = "a"
            IN two;
//          ^^ keyword.operator.word.cfml
        r = 1
            Mod two;
//          ^^^ keyword.operator.arithmetic.cfml
//              ^^^ variable.other.readwrite.cfml

        r = 1
            eq two;
//          ^^ keyword.operator.comparison.cfml
        r = 1
            NEQ two;
//          ^^^ keyword.operator.comparison.cfml
        r = 1
            equal two;
//          ^^^^^ keyword.operator.comparison.cfml
//                ^^^ variable.other.readwrite.cfml
        r = 1
            Is two;
//          ^^ keyword.operator.comparison.cfml
        r = 1
            is not two;
//          ^^^^^^ keyword.operator.comparison.cfml
        r = 1
            not equal two;
//          ^^^^^^^^^ keyword.operator.comparison.cfml
//                    ^^^ variable.other.readwrite.cfml
        r = 1
            NOT  EQUAL two;
//          ^^^^^^^^^^ keyword.operator.comparison.cfml

        r = 1
            lt two;
//          ^^ keyword.operator.comparison.cfml
        r = 1
            LTE two;
//          ^^^ keyword.operator.comparison.cfml
        r = 1
            le two;
//          ^^ keyword.operator.comparison.cfml
        r = 1
            less than two;
//          ^^^^^^^^^ keyword.operator.comparison.cfml
//                    ^^^ variable.other.readwrite.cfml
        r = 1
            Less Than Or Equal To two;
//          ^^^^^^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                                ^^^ variable.other.readwrite.cfml
        r = 1
            gt two;
//          ^^ keyword.operator.comparison.cfml
        r = 1
            gte two;
//          ^^^ keyword.operator.comparison.cfml
//              ^^^ variable.other.readwrite.cfml
        r = 1
            GE two;
//          ^^ keyword.operator.comparison.cfml
        r = 1
            greater than two;
//          ^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                       ^^^ variable.other.readwrite.cfml
        r = 1
            greater than or equal to two;
//          ^^^^^^^^^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                                   ^^^ variable.other.readwrite.cfml

        r = "one"
            contains two;
//          ^^^^^^^^ keyword.operator.comparison.cfml
        r = "one"
            CONTAINS two;
//          ^^^^^^^^ keyword.operator.comparison.cfml
        r = "one"
            does not contain two;
//          ^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                           ^^^ variable.other.readwrite.cfml
        r = "one"
            Does Not Contain two;
//          ^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
    }

    // A line that starts with a name only beginning with an operator's
    // letters, a bare `not`, or `++`/`--` starts a new statement.
    function notContinued() {
        r = 1
        android = 1;
//      ^^^^^^^ variable.other.readwrite.cfml
//              ^ keyword.operator.assignment.cfml
        r = 1
        orders = 1;
//      ^^^^^^ variable.other.readwrite.cfml
        r = 1
        island = 1;
//      ^^^^^^ variable.other.readwrite.cfml
        r = 1
        inventory = 1;
//      ^^^^^^^^^ variable.other.readwrite.cfml
        r = 1
        mode = 1;
//      ^^^^ variable.other.readwrite.cfml
        r = 1
        equalTo = 1;
//      ^^^^^^^ variable.other.readwrite.cfml
        r = 1
        notEqual = 1;
//      ^^^^^^^ variable.other.readwrite.cfml
        r = 1
        container = 1;
//      ^^^^^^^^^ variable.other.readwrite.cfml
        r = 1
        lessThan = 1;
//      ^^^^^^^^ variable.other.readwrite.cfml
        r = 1
        greater = 1;
//      ^^^^^^^ variable.other.readwrite.cfml
        r = 1
        does = 1;
//      ^^^^ variable.other.readwrite.cfml
        r = 1
        gtLimit = 1;
//      ^^^^^^^ variable.other.readwrite.cfml
        r = 1
        not done;
//      ^^^ keyword.operator.logical.cfml
//          ^^^^ variable.other.readwrite.cfml
        r = 1
        not equalTo;
//      ^^^ keyword.operator.logical.cfml
//          ^^^^^^^ variable.other.readwrite.cfml
        r = 1
        ++i;
//      ^^ keyword.operator.arithmetic.cfml
//        ^ variable.other.readwrite.cfml
        r = 1
        --i;
//      ^^ keyword.operator.arithmetic.cfml
//        ^ variable.other.readwrite.cfml
    }
}
