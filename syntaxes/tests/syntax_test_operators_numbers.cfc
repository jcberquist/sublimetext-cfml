// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f() {
        x = a ^ 2 \ 3;
//            ^ keyword.operator.arithmetic.cfml
//              ^ constant.numeric.value.cfml
//                ^ keyword.operator.arithmetic.cfml
        y = a
            \ 2;
//          ^ keyword.operator.arithmetic.cfml
//            ^ constant.numeric.value.cfml
        a++;
//       ^^ keyword.operator.arithmetic.cfml - keyword.operator.arithmetic.postfix
        a--;
//       ^^ keyword.operator.arithmetic.cfml - keyword.operator.arithmetic.postfix
        ++a;
//      ^^ keyword.operator.arithmetic.cfml

        n = 42;
//          ^^ meta.number.integer.decimal.cfml constant.numeric.value.cfml
        n = 1.5;
//          ^^^ meta.number.float.decimal.cfml constant.numeric.value.cfml
//           ^ punctuation.separator.decimal.cfml
        n = .5;
//          ^^ meta.number.float.decimal.cfml constant.numeric.value.cfml
        n = 1.5e-3;
//          ^^^^^^ meta.number.float.decimal.cfml constant.numeric.value.cfml
//                ^ punctuation.terminator.statement.cfml
        n = 2E10;
//          ^^^^ meta.number.float.decimal.cfml constant.numeric.value.cfml
        n = 0xFF;
//          ^^ meta.number.integer.hexadecimal.cfml constant.numeric.base.cfml
//            ^^ meta.number.integer.hexadecimal.cfml constant.numeric.value.cfml

        o = new component2();
//              ^^^^^^^^^^ entity.name.class.cfml
        o = new javaLoader();
//              ^^^^^^^^^^ entity.name.class.cfml
        o = new component();
//              ^^^^^^^^^ storage.type.class.cfml

        x = [1,2][1];
//          ^ meta.sequence.cfml punctuation.section.sequence.begin.cfml
//               ^ meta.brackets.cfml punctuation.section.brackets.begin.cfml
//                  ^ punctuation.terminator.statement.cfml -meta.brackets
        x = [a: 1]['a'];
//          ^^^^^^ meta.mapping.cfml
//                ^^^^^ meta.brackets.cfml
        t = ['string']['a', 'b'];
//          ^^^^^^^^^^ meta.brackets.cfml
//            ^^^^^^ storage.type.primitive.cfml
//                    ^^^^^^^^^^ meta.sequence.cfml
//                              ^ punctuation.terminator.statement.cfml -meta.sequence
        y = 1;
//      ^ variable.other.readwrite.cfml -meta.brackets
        z = a equal b AND c NOT EQUAL d;
//            ^^^^^ keyword.operator.comparison.cfml
//                    ^^^ keyword.operator.logical.cfml
//                          ^^^^^^^^^ keyword.operator.comparison.cfml
        z = a < b || c GTE d || e less than f;
//            ^ keyword.operator.comparison.cfml
//                     ^^^ keyword.operator.comparison.cfml
//                                ^^^^^^^^^ keyword.operator.comparison.cfml
        // `less than` and `greater than` end at a word boundary, whatever
        // follows them, and the longer `... or equal to` forms are one
        // operator.
        z = a less than "b";
//            ^^^^^^^^^ keyword.operator.comparison.cfml
//                     ^ - keyword.operator
//                      ^^^ string.quoted.double.cfml
        z = a LESS THAN (b);
//            ^^^^^^^^^ keyword.operator.comparison.cfml
//                     ^ - keyword.operator
//                      ^ punctuation.section.group.begin.cfml
        z = a less than 1;
//            ^^^^^^^^^ keyword.operator.comparison.cfml
//                     ^ - keyword.operator
//                      ^ constant.numeric.value.cfml
        z = a Less Than b;
//            ^^^^^^^^^ keyword.operator.comparison.cfml
//                     ^ - keyword.operator
//                      ^ variable.other.readwrite.cfml
        z = a less than
//            ^^^^^^^^^ keyword.operator.comparison.cfml
            b;
//          ^ variable.other.readwrite.cfml
        z = a greater than "b";
//            ^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                        ^ - keyword.operator
//                         ^^^ string.quoted.double.cfml
        z = a Greater Than (b);
//            ^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                        ^ - keyword.operator
//                         ^ punctuation.section.group.begin.cfml
        z = a GREATER THAN 1;
//            ^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                        ^ - keyword.operator
//                         ^ constant.numeric.value.cfml
        z = a greater than b;
//            ^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                        ^ - keyword.operator
//                         ^ variable.other.readwrite.cfml
        z = a greater than
//            ^^^^^^^^^^^^ keyword.operator.comparison.cfml
            b;
//          ^ variable.other.readwrite.cfml
        z = a less than or equal to "b";
//            ^^^^^^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                                  ^^^ string.quoted.double.cfml
        z = a Less Than Or Equal To b;
//            ^^^^^^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                                  ^ variable.other.readwrite.cfml
        z = a greater than or equal to (b);
//            ^^^^^^^^^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                                     ^ punctuation.section.group.begin.cfml
        z = a GREATER THAN OR EQUAL TO 1;
//            ^^^^^^^^^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
//                                     ^ constant.numeric.value.cfml
        s = "a" & b;
//              ^ keyword.operator.concatenation.cfml
        s &= b;
//        ^^ keyword.operator.assignment.augmented.cfml
        b = s contains "a" || s does not contain "b";
//            ^^^^^^^^ keyword.operator.comparison.cfml
//                              ^^^^^^^^^^^^^^^^ keyword.operator.comparison.cfml
    }
}
