// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
import a.b.c;
// <- meta.import.cfml keyword.control.import.cfml
//     ^^^^^ meta.import.cfml variable.other.readwrite.cfml
//          ^ punctuation.terminator.statement.cfml -meta.import
import a.b.*;
//     ^^^^ meta.import.cfml variable.other.readwrite.cfml
//         ^ meta.import.cfml constant.other.cfml
IMPORT "java.lang.String";
// <- keyword.control.import.cfml
//     ^^^^^^^^^^^^^^^^^^ meta.import.cfml string.quoted.double.cfml
component {
    import foo.Bar;
//  ^^^^^^ meta.import.cfml keyword.control.import.cfml
//         ^^^^^^^ meta.import.cfml variable.other.readwrite.cfml
    function f() {
        import taglib="/tags" prefix="t";
//      ^^^^^^ meta.tag.script.cfml entity.name.tag.script.cfml
//             ^^^^^^ meta.tag.script.cfml entity.other.attribute-name.cfml
    }
}
