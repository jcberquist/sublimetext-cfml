// SYNTAX TEST "cfml.sublime-syntax"
component extends = "root.model.text"
//        ^ meta.class.inheritance.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml
//                ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//                  ^ meta.class.inheritance.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//                   ^ meta.class.inheritance.cfml string.quoted.double.cfml entity.other.inherited-class.cfml
//                                   ^ embedding.cfml source.cfml.script meta.class.declaration.cfml -string -entity
extends = 'root.model.text'
// <- meta.class.inheritance.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml
//      ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//        ^ meta.class.inheritance.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//         ^ meta.class.inheritance.cfml string.quoted.single.cfml entity.other.inherited-class.cfml
//                         ^ embedding.cfml source.cfml.script meta.class.declaration.cfml -string -entity
extends = root.model.text
// <- meta.class.inheritance.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml
//      ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml
//        ^ meta.class.inheritance.cfml string.unquoted.cfml entity.other.inherited-class.cfml
//                       ^ embedding.cfml source.cfml.script meta.class.declaration.cfml -entity

// random comment
persistent = true {
// <- embedding.cfml source.cfml.script meta.class.declaration.cfml entity.other.attribute-name.cfml
//           ^ embedding.cfml source.cfml.script meta.class.declaration.cfml string.unquoted.cfml
//                ^ embedding.cfml source.cfml.script -meta.class.declaration.cfml meta.class.body.cfml punctuation.section.block.cfml
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

    arrayAppend( arr, item, true );
//             ^ meta.function-call.support.cfml meta.function-call.parameters.support.cfml punctuation.section.group.begin.cfml
//                  ^ punctuation.separator.function-call.support.cfml
    arr.append( item, true );
//            ^ meta.function-call.method.support.cfml meta.function-call.parameters.method.support.cfml punctuation.section.group.begin.cfml
//                  ^ punctuation.separator.function-call.method.support.cfml
    doSomething( arr, item, true );
//             ^ meta.function-call.cfml meta.function-call.parameters.cfml punctuation.section.group.begin.cfml
//                  ^ punctuation.separator.function-call.cfml
    obj.do( arr, item, true );
//        ^ meta.function-call.method.cfml meta.function-call.parameters.method.cfml punctuation.section.group.begin.cfml
//             ^ punctuation.separator.function-call.method.cfml

    toString( testVar, "utf-8" );
//          ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.support.cfml meta.function-call.parameters.support.cfml punctuation.section.group.begin.cfml
//                             ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.support.cfml meta.function-call.parameters.support.cfml punctuation.section.group.end.cfml
    var new_list = testVar.listAppend( "hello" );
//                         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.support.cfml support.function.member.cfml
//                                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.support.cfml meta.function-call.parameters.method.support.cfml punctuation.section.group.begin.cfml
    if ( true ) http url="www.google.com" result="result";
//              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.tag.script.cfml entity.name.tag.script.cfml
//                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.tag.script.cfml entity.other.attribute-name.cfml
    var test = "#foo
//              ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.string.quoted.double.cfml punctuation.definition.template-expression.begin.cfml
    # true";

    foo = document;
//        ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml - meta.tag.script.cfml
    foo = test.document;
//             ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml - meta.tag.script.cfml
    for ( var header in foo)
//            ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml - meta.tag.script.cfml

    test.foo( myvar == test );
//            ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.cfml meta.function-call.parameters.method.cfml variable.other.readwrite.cfml

    foo.method(test = true, random = "string");
//      ^ meta.function-call.method.cfml
//            ^ meta.function-call.method.cfml meta.function-call.parameters.method.cfml punctuation.section.group.begin.cfml
//             ^ meta.function-call.method.cfml meta.function-call.parameters.method.cfml entity.other.method-parameter.cfml
//                  ^ meta.function-call.method.cfml meta.function-call.parameters.method.cfml keyword.operator.assignment.binary.cfml
    var mycfc = createObject( 'component', 'path.to.cfc' );
//              ^ meta.function-call.support.cfml meta.function-call.support.createcomponent.cfml support.function.cfml
    var mycfc = new path.to.cfc(test = true, random = "string");
//              ^ meta.instance.constructor.cfml keyword.operator.word.new.cfml
//                          ^ meta.instance.constructor.cfml entity.name.class.cfml
//                             ^ meta.instance.constructor.cfml meta.function-call.parameters.method.cfml punctuation.section.group.begin.cfml
//                              ^ meta.instance.constructor.cfml meta.function-call.parameters.method.cfml entity.other.method-parameter.cfml
//                                   ^  meta.instance.constructor.cfml meta.function-call.parameters.method.cfml keyword.operator.assignment.binary.cfml
    new path.to.cfc().callmethod();
//                   ^ punctuation.accessor.cfml
//                    ^ meta.function-call.method.cfml
    var mystring = createobject( "java", "java.lang.String" );
//                 ^ meta.function-call.support.cfml meta.function-call.support.createjavaobject.cfml support.function.cfml
    return result = foo;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
//                  ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
    return result == test ? 'one' : 2;
//         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
//                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml variable.other.readwrite.cfml
//                        ^ keyword.operator.ternary.cfml
//                                ^ keyword.operator.ternary.cfml

  var test = {
    1: true ? 1 : 0,
    2: test
//  ^ meta.struct-literal.key.cfml -constant.numeric.cfml
  }

    throw( message = "test error message" );
//  ^ meta.function-call.support.cfml support.function.cfml
//       ^ meta.function-call.support.cfml meta.function-call.parameters.support.cfml punctuation.section.group.begin.cfml -support.function.cfml
//         ^ meta.function-call.parameters.support.cfml entity.other.function-parameter.cfml -meta.brace

    myarray.append( value = 'test' );
//  ^ variable.other.object.cfml
//          ^ meta.function-call.method.support.cfml support.function.member.cfml
//                ^ meta.function-call.method.support.cfml meta.function-call.parameters.method.support.cfml punctuation.section.group.begin.cfml
//                  ^ meta.function-call.method.support.cfml meta.function-call.parameters.method.support.cfml entity.other.method-parameter.cfml -meta.brace

    return { key: value };
//         ^ meta.struct-literal.cfml

  }

  public User[] function getUser(){}
//^ meta.function.declaration.cfml storage.modifier.cfml
//       ^ meta.function.declaration.cfml storage.type.return-type.object.array.cfml
//           ^ meta.function.declaration.cfml meta.brackets.cfml punctuation.section.brackets.begin.cfml

  function go( required string param = someVar & hint hint="go", param_2 ) {}
//           ^^^^ meta.function.declaration.cfml
//                                               ^ meta.parameter.optional.cfml variable.other.readwrite.cfml
//                                                    ^ entity.other.attribute-name.cfml
//                                                        ^ punctuation.separator.key-value.cfml
//                                                         ^ string.quoted.double.cfml punctuation.definition.string.begin.cfml

  function go( required string param = true ) {}
//^ storage.type.function.cfml
//                                     ^ meta.parameter.optional.cfml constant.language.boolean.true.cfml

public void function setup( required root.model.cava.connection connection ) {}
//                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^ variable.parameter.function.cfml

  void function testme() hint="testme" {}
//^ meta.function.declaration.cfml storage.type.return-type.void.cfml
//                       ^ meta.function.declaration.cfml
//                       ^ -meta.function.declaration.cfml meta.function.declaration.cfml

  var test = {
    key: value,
//  ^ meta.struct-literal.key.cfml
//     ^ punctuation.separator.key-value.cfml
//            ^ punctuation.separator.struct-literal.cfml
    'key': value,
//  ^ meta.struct-literal.key.cfml string.quoted.single.cfml
//       ^ punctuation.separator.key-value.cfml -string
    "key": value,
//  ^ meta.struct-literal.key.cfml string.quoted.double.cfml
//       ^ punctuation.separator.key-value.cfml -string
    key = value,
//  ^ meta.struct-literal.key.cfml -entity.name.function
//      ^ punctuation.separator.key-value.cfml
    'key' = value,
//  ^^^^^ meta.struct-literal.key.cfml string.quoted.single.cfml
//        ^ punctuation.separator.key-value.cfml -string
    "key" = value,
//  ^^^^^ meta.struct-literal.key.cfml string.quoted.double.cfml
//        ^ punctuation.separator.key-value.cfml -string
    456: 'A valid struct',
//  ^^^ meta.struct-literal.key.cfml
//     ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
//                       ^ punctuation.separator.struct-literal.cfml
    key: function() {},
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ meta.function.declaration.cfml punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
//                    ^ punctuation.separator.struct-literal.cfml
    "key": function() {},
//   ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.double.cfml entity.name.function.cfml
//       ^ meta.function.declaration.cfml punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
    'key': function() {}
//   ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.single.cfml entity.name.function.cfml
//       ^ meta.function.declaration.cfml punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml

  }

  switch( foo ) {
//^ meta.switch.cfml keyword.control.switch.cfml
//              ^ meta.switch.cfml punctuation.section.block.begin.cfml
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

  var test[key][0] = [ 1, 2, 3 ];
//        ^^^^^^^^ meta.brackets.cfml
//                   ^^^^^^^^^^^ meta.array-literal.cfml
//                      ^ punctuation.separator.array-literal.cfml
  obj.prop['key'] = true;
//        ^^^^^^^ meta.brackets.cfml

  thisQuery = queryExecute("SELECT * from myTable WHERE myColumn = 1", "SELECT * from myTable WHERE myColumn = 1");
//                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml
//                                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml
  thisQuery = queryExecute(params = {}, sql = "SELECT * FROM myTable");
//                                             ^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml
  var test = "FROM myTable WHERE test = '#obj.property#'"
//            ^^^^ meta.string.quoted.double.cfml source.sql keyword.other.DML.sql
//                                            ^^^^^^^^ source.cfml.script source.sql source.cfml.script meta.property.cfml
  var test3 = entityLoadByPK( "foo", "someId" );
//            ^ meta.function-call.support.cfml meta.function-call.support.entity.cfml support.function.cfml
  var test4 = entityLoad( "foo", {}, true );
//            ^ meta.function-call.support.cfml meta.function-call.support.entity.cfml support.function.cfml
  var test5 = entityNew( "foo" );
//            ^ meta.function-call.support.cfml meta.function-call.support.entity.cfml support.function.cfml

  new 123Foo();
//    ^^^^^^ source.cfml.script meta.class.body.cfml meta.instance.constructor.cfml entity.name.class.cfml

  new 1path.123Foo();
//    ^^^^^^^^^^^^ source.cfml.script meta.class.body.cfml meta.instance.constructor.cfml entity.name.class.cfml

  new .foo();
//    ^ source.cfml.script meta.class.body.cfml punctuation.accessor.cfml
//     ^^^ meta.function-call.method.cfml variable.function.cfml

  this.test = function() {};
//    ^ punctuation.accessor.cfml
  this.test();
//    ^ punctuation.accessor.cfml
}
// <- embedding.cfml source.cfml.script meta.class.body.cfml punctuation.section.block.end.cfml
 // <- embedding.cfml source.cfml.script -meta
