// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f() {
        writeOutput(catch.message);
//                  ^^^^^ variable.other.object.cfml -keyword
//                        ^^^^^^^ variable.other.member.cfml
        catch.detail = "x";
//      ^^^^^ variable.other.object.cfml -keyword
        out &= case;
//             ^^^^ variable.other.readwrite.cfml -keyword
        var in = 1;
//          ^^ meta.binding.name.cfml variable.other.readwrite.cfml
        var case = 2;
//          ^^^^ meta.binding.name.cfml variable.other.readwrite.cfml
        switch = 3;
//      ^^^^^^ variable.other.readwrite.cfml -keyword
        try {} catch (any e) {}
//             ^^^^^ keyword.control.exception.catch.cfml
        return;
//      ^^^^^^ keyword.control.flow.return.cfml
        for (k in s) {}
//             ^^ keyword.operator.word.cfml
        if (a) {} else {}
//                ^^^^ keyword.control.conditional.else.cfml
        switch (x) { case 1: break; }
//                   ^^^^ keyword.control.conditional.case.cfml
    }
}
