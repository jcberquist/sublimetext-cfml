// SYNTAX TEST "cfml.tmLanguage"
component extends = "root.model.text"
//        ^ meta.class.inheritance.cfml storage.modifier.extends.cfml
//                ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//                  ^ meta.class.inheritance.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//                   ^ meta.class.inheritance.cfml string.quoted.double.cfml entity.other.inherited-class.cfml
//                                   ^ embedding.cfml source.cfml.script meta.class.declaration.cfml -string -entity
extends = 'root.model.text'
// <- meta.class.inheritance.cfml storage.modifier.extends.cfml
//      ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//        ^ meta.class.inheritance.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//         ^ meta.class.inheritance.cfml string.quoted.single.cfml entity.other.inherited-class.cfml
//                         ^ embedding.cfml source.cfml.script meta.class.declaration.cfml -string -entity
extends = root.model.text
// <- meta.class.inheritance.cfml storage.modifier.extends.cfml
//      ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//        ^ meta.class.inheritance.cfml string.unquoted.cfml entity.other.inherited-class.cfml
//                       ^ embedding.cfml source.cfml.script meta.class.declaration.cfml -entity

// random comment
persistent = true {
// <- embedding.cfml source.cfml.script meta.class.declaration.cfml entity.other.attribute-name.cfml
//           ^ embedding.cfml source.cfml.script meta.class.declaration.cfml string.unquoted.cfml
//                ^ embedding.cfml source.cfml.script -meta.class.declaration.cfml meta.class.body.cfml punctuation.definition.block.cfml
  property test;
// <- embedding.cfml source.cfml.script meta.class.body.cfml
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
  property test test;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml storage.type.cfml
//              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
  property test test test;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml storage.type.cfml
//              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
//                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml entity.other.attribute-name.cfml
  property name="test" required=true;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml entity.other.attribute-name.cfml
//               ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml string.quoted.double.cfml meta.tag.property.name.cfml
//                              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml string.unquoted.cfml
//                                  ^ embedding.cfml source.cfml.script meta.class.body.cfml punctuation.terminator.statement.cfml
  property
    name = "test"
    required=true;
//  ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml entity.other.attribute-name.cfml
//           ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml string.unquoted.cfml
  property test
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml meta.tag.property.cfml string.unquoted.cfml meta.tag.property.name.cfml
default="string";
// <- embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml entity.other.attribute-name.cfml
//       ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml string.quoted.double.cfml

  public string function foo() {
// <- embedding.cfml source.cfml.script meta.class.body.cfml - meta.function.declaration.cfml
//^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.declaration.cfml
    var result;

    toString( testVar, "utf-8" );
//  ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.support.function-call.cfml support.function.cfml
//          ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.support.function-call.cfml meta.support.function-call.arguments.cfml punctuation.definition.group.begin.cfml
//                             ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.support.function-call.cfml meta.support.function-call.arguments.cfml punctuation.definition.group.end.cfml
    var new_list = testVar.listAppend( "hello" );
//                         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.support.function-call.member.cfml support.function.member.cfml
//                                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.support.function-call.member.cfml meta.support.function-call.member.arguments.cfml punctuation.definition.group.begin.cfml
    if ( true ) http url="www.google.com" result="result";
//              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.tag.script.cfml entity.name.tag.script.cfml
//                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml entity.other.attribute-name.cfml
    var test = "#foo
//              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml string.quoted.double.cfml constant.character.hash.cfml
    # true";

    foo = document;
//        ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml - meta.tag.script.cfml
    foo = test.document;
//             ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml - meta.tag.script.cfml
    for ( var header in foo)
//            ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml - meta.tag.script.cfml

    test.foo( myvar == test );
//            ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.cfml meta.function-call.method.arguments.cfml variable.other.readwrite.cfml

    foo.method(test = true, random = "string");
//      ^ meta.function-call.method.cfml
//            ^ meta.function-call.method.cfml meta.function-call.method.arguments.cfml punctuation.definition.group.begin.cfml
//             ^ meta.function-call.method.cfml meta.function-call.method.arguments.cfml entity.other.method-parameter.cfml
//                  ^ meta.function-call.method.cfml meta.function-call.method.arguments.cfml keyword.operator.assignment.cfml
    var mycfc = createObject( 'component', 'path.to.cfc' );
//              ^ meta.support.function-call.cfml meta.support.function-call.createcomponent.cfml support.function.cfml
    var mycfc = new path.to.cfc(test = true, random = "string");
//              ^ meta.instance.constructor.cfml keyword.operator.new.cfml
//                          ^ meta.instance.constructor.cfml entity.name.class.cfml
//                             ^ meta.instance.constructor.cfml meta.function-call.method.arguments.cfml punctuation.definition.group.begin.cfml
//                              ^ meta.instance.constructor.cfml meta.function-call.method.arguments.cfml entity.other.method-parameter.cfml
//                                   ^  meta.instance.constructor.cfml meta.function-call.method.arguments.cfml keyword.operator.assignment.cfml
    new path.to.cfc().callmethod();
//                   ^ punctuation.accessor.cfml
//                    ^ meta.function-call.method.cfml
    var mystring = createobject( "java", "java.lang.String" );
//                 ^ meta.support.function-call.cfml meta.support.function-call.createjavaobject.cfml support.function.cfml
    return result = foo;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
//                  ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
    return result == test ? 'one' : 2;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
//                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
//                        ^ keyword.operator.ternary.cfml
//                                ^ keyword.operator.ternary.cfml

    throw( message = "test error message" );
//  ^ meta.support.function-call.cfml support.function.cfml
//       ^ meta.support.function-call.cfml meta.support.function-call.arguments.cfml punctuation.definition.group.begin.cfml -support.function.cfml
//         ^ meta.support.function-call.arguments.cfml entity.other.function-parameter.cfml -meta.brace

    myarray.append( value = 'test' );
//  ^ variable.other.object.cfml
//          ^ meta.support.function-call.member.cfml support.function.member.cfml
//                ^ meta.support.function-call.member.cfml meta.support.function-call.member.arguments.cfml punctuation.definition.group.begin.cfml
//                  ^ meta.support.function-call.member.cfml meta.support.function-call.member.arguments.cfml entity.other.method-parameter.cfml -meta.brace

  }

  public User[] function getUser(){}
//^ meta.function.declaration.cfml storage.modifier.cfml
//       ^ meta.function.declaration.cfml storage.type.return-type.object.array.cfml
//           ^ meta.function.declaration.cfml meta.brackets.cfml punctuation.definition.brackets.begin.cfml

  var test = {
    key: value,
//  ^ meta.struct-literal.key.cfml
//     ^ punctuation.separator.key-value.cfml
    'key': value,
//  ^ meta.struct-literal.key.cfml string.quoted.single.cfml
//       ^ punctuation.separator.key-value.cfml -string
    "key": value,
//  ^ meta.struct-literal.key.cfml string.quoted.double.cfml
//       ^ punctuation.separator.key-value.cfml -string
    key = value,
//  ^ meta.struct-literal.key.cfml
//      ^ punctuation.separator.key-value.cfml
    'key' = value,
//  ^ meta.struct-literal.key.cfml string.quoted.single.cfml
//        ^ punctuation.separator.key-value.cfml -string
    "key" = value,
//  ^ meta.struct-literal.key.cfml string.quoted.double.cfml
//        ^ punctuation.separator.key-value.cfml -string
    key: function() {},
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ meta.function.declaration.cfml punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
    "key": function() {},
//   ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.double.cfml entity.name.function.cfml
//       ^ meta.function.declaration.cfml punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
    'key': function() {}
//   ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.single.cfml entity.name.function.cfml
//       ^ meta.function.declaration.cfml punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml

  }

  switch( foo ) {
//^ meta.switch.cfml keyword.control.switch.cfml
//              ^ meta.switch.cfml punctuation.definition.block.begin.cfml
    case "baz":
//  ^ meta.switch.cfml keyword.control.switch.cfml
//        ^ meta.switch.cfml string.quoted.double.cfml
    break;
//  ^ meta.switch.cfml keyword.control.loop.cfml
    default:
//  ^ meta.switch.cfml keyword.control.switch.cfml
  }

  var test = function() { return foo; };
//    ^ meta.function.declaration.cfml variable.other.readwrite.cfml entity.name.function.cfml

  obj.prop = true;
  // <- variable.other.struct.cfml
//    ^ meta.property.cfml
  obj.CONSTANT = true;
  // <- variable.other.struct.cfml
//    ^ meta.property.constant.cfml

}
// <- embedding.cfml source.cfml.script meta.class.body.cfml punctuation.definition.block.end.cfml
 // <- embedding.cfml source.cfml.script -meta