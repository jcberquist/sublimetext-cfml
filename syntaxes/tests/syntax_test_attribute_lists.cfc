// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
interface {
    function f()
//           ^ meta.function.declaration.cfml entity.name.function.cfml
    function g();
//  ^^^^^^^^ meta.function.declaration.cfml storage.type.function.cfml
//           ^ meta.function.declaration.cfml entity.name.function.cfml
    public string function h() output=false
//                             ^^^^^^ meta.function.declaration.cfml entity.other.attribute-name.cfml
    function i() {}
//           ^ meta.function.declaration.cfml entity.name.function.cfml
}
x = 1;
// <- variable.other.readwrite.cfml -meta.interface
component {
    function j() description="multi"
        hint="line"
//      ^^^^ meta.function.declaration.cfml entity.other.attribute-name.cfml
    {
//  ^ meta.function.body.cfml punctuation.section.block.begin.cfml
    }
    property name="a"
//           ^^^^ meta.tag.property.cfml entity.other.attribute-name.cfml
    foo();
//  ^^^ meta.function-call.cfml variable.function.cfml -meta.tag
    property name="b"
        type="string";
//      ^^^^ meta.tag.property.cfml entity.other.attribute-name.cfml
    param name="p" default="1"
    return;
//  ^^^^^^ keyword.control.flow.return.cfml -meta.tag
}
interface {
// <- meta.interface.declaration.cfml storage.type.interface.cfml keyword.declaration.interface.cfml
}
