// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f() {
        x = a ^ 2 \ 3;
//            ^ keyword.operator.arithmetic.binary.cfml
//              ^ constant.numeric.value.cfml
//                ^ keyword.operator.arithmetic.binary.cfml
        y = a
            \ 2;
//          ^ keyword.operator.arithmetic.binary.cfml
//            ^ constant.numeric.value.cfml

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
//            ^^^^^ keyword.operator.comparison.binary.cfml
//                    ^^^ keyword.operator.logical.binary.cfml
//                          ^^^^^^^^^ keyword.operator.comparison.binary.cfml
    }
}
