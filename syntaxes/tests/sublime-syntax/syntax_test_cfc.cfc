// SYNTAX TEST "cfml.sublime-syntax"
component extends = "root.model.text"
//        ^ meta.class.inheritance.cfml storage.modifier.extends.cfml
//                ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//                  ^ meta.class.inheritance.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//                   ^ meta.class.inheritance.cfml string.quoted.double.cfml entity.other.inherited-class.cfml
//                                   ^ embedding.cfml source.cfml.script meta.class.cfml
extends = 'root.model.text'
// <- meta.class.inheritance.cfml storage.modifier.extends.cfml
//      ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//        ^ meta.class.inheritance.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//         ^ meta.class.inheritance.cfml string.quoted.single.cfml entity.other.inherited-class.cfml
//                         ^ embedding.cfml source.cfml.script meta.class.cfml
extends = root.model.text
// <- meta.class.inheritance.cfml storage.modifier.extends.cfml
//      ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//        ^ meta.class.inheritance.cfml string.unquoted.cfml entity.other.inherited-class.cfml
//                       ^ embedding.cfml source.cfml.script meta.class.cfml

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

    foo.method(test = true, random = "string");
//      ^ meta.function-call.method.cfml
//            ^ meta.function-call.method.cfml meta.function-call.method.arguments.cfml punctuation.definition.arguments.begin.cfml
//             ^ meta.function-call.method.cfml meta.function-call.method.arguments.cfml entity.other.method-parameter.cfml
//                  ^ meta.function-call.method.cfml meta.function-call.method.arguments.cfml keyword.operator.assignment.cfml
    var mycfc = createObject( 'component', 'path.to.cfc' );
//              ^ meta.support.function-call.cfml meta.support.function-call.createcomponent.cfml support.function.cfml
    var mycfc = new path.to.cfc(test = true, random = "string");
//              ^ meta.instance.constructor keyword.operator.new.cfml
//                          ^ meta.instance.constructor entity.name.class.cfml
//                             ^ meta.instance.constructor meta.function-call.method.arguments.cfml punctuation.definition.arguments.begin.cfml
//                              ^ meta.instance.constructor meta.function-call.method.arguments.cfml entity.other.method-parameter.cfml
//                                   ^  meta.instance.constructor meta.function-call.method.arguments.cfml keyword.operator.assignment.cfml
    new path.to.cfc().callmethod();
//                   ^ keyword.operator.accessor.cfml
//                    ^ meta.function-call.method.cfml
    var mystring = createobject( "java", "java.lang.String" );
//                 ^ meta.support.function-call.cfml meta.support.function-call.createjavaobject.cfml support.function.cfml
    return result = foo;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
//                  ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
    return result == test ? 'one' : 2;
//         ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml
//                   ^ embedding.cfml source.cfml.script meta.group.braces.curly meta.group.braces.curly variable.other.cfml

    throw( message = "test error message" );
//  ^ meta.support.function-call.cfml support.function.cfml
  }

  public User[] function getUser(){}
//^ meta.function.cfml storage.modifier.cfml
//       ^ meta.function.cfml storage.type.return-type.object.array.cfml
//           ^ meta.function.cfml meta.group.braces.square meta.brace.square.cfml

}