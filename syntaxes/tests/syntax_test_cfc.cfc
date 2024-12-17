// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
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
//             ^ meta.function-call.support.cfml meta.function-call.arguments.support.cfml punctuation.section.group.begin.cfml
//                  ^ punctuation.separator.function-call.support.cfml
    arr.append( item, true );
//            ^ meta.function-call.method.support.cfml meta.function-call.arguments.method.support.cfml punctuation.section.group.begin.cfml
//                  ^ punctuation.separator.function-call.method.support.cfml
    doSomething( arr, item, true );
//             ^ meta.function-call.cfml meta.function-call.arguments.cfml punctuation.section.group.begin.cfml
//                  ^ punctuation.separator.function-call.cfml
    $$badRequest();
//              ^ meta.function-call.cfml meta.function-call.arguments.cfml punctuation.section.group.begin.cfml
//
    obj.do( arr, item, true );
//        ^ meta.function-call.method.cfml meta.function-call.arguments.method.cfml punctuation.section.group.begin.cfml
//             ^ punctuation.separator.function-call.method.cfml

    toString( testVar, "utf-8" );
//          ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.support.cfml meta.function-call.arguments.support.cfml punctuation.section.group.begin.cfml
//                             ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.support.cfml meta.function-call.arguments.support.cfml punctuation.section.group.end.cfml
    var new_list = testVar.listAppend( "hello" );
//                         ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.support.cfml support.function.member.cfml
//                                   ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.support.cfml meta.function-call.arguments.method.support.cfml punctuation.section.group.begin.cfml
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
//            ^ embedding.cfml source.cfml.script meta.class.body.cfml meta.function.body.cfml meta.function-call.method.cfml meta.function-call.arguments.method.cfml variable.other.readwrite.cfml

    foo.method(test = true, random = "string");
//      ^ meta.function-call.method.cfml
//            ^ meta.function-call.method.cfml meta.function-call.arguments.method.cfml punctuation.section.group.begin.cfml
//             ^ meta.function-call.method.cfml meta.function-call.arguments.method.cfml entity.other.method-parameter.cfml
//                  ^ meta.function-call.method.cfml meta.function-call.arguments.method.cfml keyword.operator.assignment.cfml
    var mycfc = createObject( 'component', 'path.to.cfc' );
//              ^ meta.function-call.support.cfml meta.function-call.support.createcomponent.cfml support.function.cfml
    var mycfc = new path.to.cfc(test = true, random = "string");
//              ^ meta.instance.constructor.cfml keyword.operator.word.new.cfml
//                          ^ meta.instance.constructor.cfml entity.name.class.cfml
//                             ^ meta.instance.constructor.cfml meta.function-call.arguments.method.cfml punctuation.section.group.begin.cfml
//                              ^ meta.instance.constructor.cfml meta.function-call.arguments.method.cfml entity.other.method-parameter.cfml
//                                   ^  meta.instance.constructor.cfml meta.function-call.arguments.method.cfml keyword.operator.assignment.cfml
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
//       ^ meta.function-call.support.cfml meta.function-call.arguments.support.cfml punctuation.section.group.begin.cfml -support.function.cfml
//         ^ meta.function-call.arguments.support.cfml entity.other.function-parameter.cfml -meta.brace

    throw "test error message";
//  ^^^^^ keyword.control.flow.throw.cfml

    abort;
//  ^^^^^ keyword.control.flow.cfml

    include '#template#';
//  ^^^^^^^ keyword.control.flow.cfml

    include myvar;
//  ^^^^^^^ keyword.control.flow.cfml

    include template='';
//  ^^^^^^^ meta.tag.script.cfml entity.name.tag.script.cfml

    myarray.append( value = 'test' );
//  ^ variable.other.object.cfml
//          ^ meta.function-call.method.support.cfml support.function.member.cfml
//                ^ meta.function-call.method.support.cfml meta.function-call.arguments.method.support.cfml punctuation.section.group.begin.cfml
//                  ^ meta.function-call.method.support.cfml meta.function-call.arguments.method.support.cfml entity.other.method-parameter.cfml -meta.brace

    return { key: value };
//         ^ meta.struct-literal.cfml

  }

  public User[] function getUser(){}
//^ meta.function.declaration.cfml storage.modifier.cfml
//       ^ meta.function.declaration.cfml storage.type.object.array.cfml
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
//                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^ storage.type.cfml
//                                                              ^^^^^^^^^^ variable.parameter.function.cfml

private numeric function $fixNumber(required any value) {}
//                       ^^^^^^^^^^ entity.name.function.cfml

  void function testme() hint="testme" {}
//^ meta.function.declaration.cfml storage.type.void.cfml
//                       ^ meta.function.declaration.cfml
//                       ^ -meta.function.declaration.cfml meta.function.declaration.cfml

_foo function test() {}
// <- meta.function.declaration.cfml storage.type.object.cfml

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
//  ^ meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
//                    ^ punctuation.separator.struct-literal.cfml
    "key": function() {},
//   ^ meta.struct-literal.key.cfml string.quoted.double.cfml entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml
    'key': function() {}
//   ^ meta.struct-literal.key.cfml string.quoted.single.cfml entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml

  }

  switch( foo ) {
//^ meta.switch.cfml keyword.control.conditional.switch.cfml
//              ^ meta.switch.cfml punctuation.section.block.begin.cfml
    case "baz":
//  ^ meta.switch.cfml keyword.control.conditional.case.cfml
//        ^ meta.switch.cfml string.quoted.double.cfml
    break;
//  ^ meta.switch.cfml keyword.control.flow.break.cfml 
    default:
//  ^ meta.switch.cfml keyword.control.conditional.default.cfml 
  }

  var test = function() { return foo; };
//    ^ entity.name.function.cfml variable.other.readwrite.cfml

  obj.prop = true;
  // <- variable.other.object.cfml
//    ^ meta.property.cfml
  obj.CONSTANT = true;
  // <- variable.other.object.cfml
//    ^ meta.property.constant.cfml

  var test[key][0] = [ 1, 2, 3 ];
//        ^^^^^^^^ meta.brackets.cfml
//                   ^^^^^^^^^^^ meta.sequence.cfml
//                      ^ punctuation.separator.sequence.cfml
  obj.prop['key'] = true;
//        ^^^^^^^ meta.brackets.cfml

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
cflock(name:"name-of-lock") {}
//    ^ meta.tag.script.cf.cfml  meta.tag.script.cf.attributes.cfml punctuation.section.group.begin.cfml
//         ^ meta.tag.script.cf.cfml punctuation.separator.key-value.cfml
//          ^ meta.string.quoted.double.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//           ^^^^^^^^^^^^ meta.string.quoted.double.cfml string.quoted.double.cfml
//                        ^ meta.tag.script.cf.cfml  meta.tag.script.cf.attributes.cfml punctuation.section.group.end.cfml
//                          ^ meta.block.cfml punctuation.section.block.begin.cfml
  test(name:"arg");
//     ^^^^ entity.other.function-parameter.cfml
//         ^ punctuation.separator.key-value.cfml
}
// <- embedding.cfml source.cfml.script meta.class.body.cfml punctuation.section.block.end.cfml
 // <- embedding.cfml source.cfml.script -meta

a = arrayNew["string"](1);
//  ^^^^^^^^ source.cfml.script support.function.cfml
//          ^ source.cfml.script meta.brackets.cfml punctuation.section.brackets.begin.cfml
//            ^^^^^^ meta.brackets.cfml meta.string.quoted.double.cfml string.quoted.double.cfml storage.type.primitive.cfml

a = ['string']["a", "b"];
//    ^^^^^^ meta.brackets.cfml meta.string.quoted.single.cfml string.quoted.single.cfml storage.type.primitive.cfml
//            ^^^^^^^^^^ source.cfml.script meta.sequence.cfml

a = [
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
];

a = 'a #test# string';
//     ^ punctuation.definition.template-expression.begin.cfml
//          ^ punctuation.definition.template-expression.end.cfml

a = [:];
//   ^ punctuation.separator.key-value.cfml

try {
} catch (any e) {
//       ^^^ support.type.exception.cfml
//           ^ variable.other.readwrite.cfml
} catch (var e) {
//       ^^^ support.type.exception.cfml
//           ^ variable.other.readwrite.cfml
} catch (any var e) {
//       ^^^ support.type.exception.cfml
//           ^^^ storage.type.cfml
//               ^ variable.other.readwrite.cfml
} catch (java.lang.ThreadDeath e) {
//       ^^^^^^^^^^^^^^^^^^^^^ support.type.exception.cfml
//                             ^ variable.other.readwrite.cfml
}

if (a <> b) {}
//    ^^ source.cfml.script meta.conditional.cfml meta.group.cfml keyword.operator.comparison.binary.cfml


variables?.foo?.bar;
//       ^^ punctuation.accessor.safe.cfml
//            ^^ punctuation.accessor.safe.cfml
getFoo()?.getBar();
//      ^^ punctuation.accessor.safe.cfml
test?.foo();
// <- variable.other.object.cfml

a = 10 mod 5;
//     ^^^ keyword.operator.arithmetic.binary.cfml

for (var ieeetype IN Dictionary().ieeetypes);
//                ^^ keyword.operator.binary.cfml
