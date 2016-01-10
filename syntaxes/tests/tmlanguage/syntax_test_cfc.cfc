// SYNTAX TEST "cfml.tmLanguage"
component extends = "root.model.text"
// random comment
persistent = true {
// <- embedding.cfml source.cfml.script meta.class.cfml entity.other.attribute-name.cfml
//           ^ embedding.cfml source.cfml.script meta.class.cfml string.unquoted.cfml
  property test;
// <- embedding.cfml source.cfml.script meta.group.braces.curly - meta.tag.script.cfml
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
  property test test;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml storage.type.cfml
//              ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
  property test test test;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml storage.type.cfml
//              ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
//                   ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml entity.other.attribute-name.cfml
  property name="test" required=true;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml entity.other.attribute-name.cfml
//               ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml string.quoted.double.cfml
//                              ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml string.unquoted.cfml
//                                  ^ embedding.cfml source.cfml.script meta.group.braces.curly punctuation.terminator.statement.cfml
  property
    name = "test"
    required=true;
//  ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml entity.other.attribute-name.cfml
//           ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml string.unquoted.cfml
  property test
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
default="string";
// <- embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml entity.other.attribute-name.cfml
//       ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml string.quoted.double.cfml

  public string function foo() {
// <- embedding.cfml source.cfml.script meta.group.braces.curly - meta.function.cfml
//^ embedding.cfml source.cfml.script meta.group.braces.curly meta.function.cfml
    var result;

    toString( testVar, "utf-8" );
//  ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.support.function-call.cfml support.function.cfml
//          ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.support.function-call.cfml meta.support.function-call.arguments.cfml punctuation.definition.arguments.begin.cfml
//                             ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.support.function-call.arguments.cfml punctuation.definition.arguments.end.cfml
    var new_list = testVar.listAppend( "hello" );
//                         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.support.function-call.member.cfml support.function.member.cfml
//                                   ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.support.function-call.member.cfml meta.support.function-call.member.arguments.cfml punctuation.definition.arguments.begin.cfml
    if ( true ) http url="www.google.com" result="result";
//              ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.tag.script.cfml entity.name.tag.script.cfml
//                   ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.tag.script.cfml entity.other.attribute-name.cfml
    var test = "#foo
//              ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly string.quoted.double.cfml constant.character.hash.cfml
    # true";

    foo = document;
//        ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly - meta.tag.script.cfml
    foo = test.document;
//             ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly - meta.tag.script.cfml
    for ( var header in foo)
//            ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly - meta.tag.script.cfml

    test.foo( myvar == test );
//            ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly meta.function-call.method.cfml meta.function-call.method.arguments.cfml variable.other.cfml

    return result = foo;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
//                  ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
    return result == test ? 'one' : 2;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
//                   ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
  }

}