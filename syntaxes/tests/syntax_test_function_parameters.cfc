// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f(required string a key=true, string b other=x.y) {
//                               ^^^ entity.other.attribute-name.cfml
//                                   ^^^^ string.unquoted.cfml
//                                       ^ punctuation.separator.parameter.function.cfml
//                                                        ^^^ string.unquoted.cfml
//                                                           ^ punctuation.section.parameters.end.cfml
//                                                             ^ meta.function.body.cfml punctuation.section.block.begin.cfml
        return 1;
//      ^^^^^^ keyword.control.flow.return.cfml
    }
    x = 1;
//  ^ variable.other.readwrite.cfml

    private string[] function b() {}
//          ^^^^^^ meta.function.declaration.cfml storage.type.primitive.cfml
//                ^^ meta.function.declaration.cfml meta.brackets.cfml
//                   ^^^^^^^^ storage.type.function.cfml
//                            ^ entity.name.function.cfml
    public Foo[] function c() {}
//         ^^^ storage.type.object.array.cfml
//                        ^ entity.name.function.cfml
}
component {
    function map(required required=true, required string name) {}
//               ^^^^^^^^ meta.function.parameters.cfml keyword.other.required.parameter.cfml
//                        ^^^^^^^^ meta.function.parameters.cfml variable.parameter.function.cfml
//                                ^ meta.function.parameters.cfml keyword.operator.assignment.cfml
//                                       ^^^^^^^^ meta.function.parameters.cfml keyword.other.required.parameter.cfml
//                                                       ^^^^ meta.function.parameters.cfml variable.parameter.function.cfml
}
