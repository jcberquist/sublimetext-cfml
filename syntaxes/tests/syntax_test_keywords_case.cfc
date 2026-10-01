// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    PUBLIC STATIC STRING FUNCTION foo() {}
//  ^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//         ^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//                ^^^^^^ meta.function.declaration.cfml storage.type.primitive.cfml
//                       ^^^^^^^^ meta.function.declaration.cfml storage.type.function.cfml
//                                ^^^ meta.function.declaration.cfml entity.name.function.cfml

    static public struct function two() {}
//  ^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//         ^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//                ^^^^^^ meta.function.declaration.cfml storage.type.primitive.cfml
//                                ^^^ meta.function.declaration.cfml entity.name.function.cfml
    final public string function three() {}
//  ^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//                               ^^^^^ meta.function.declaration.cfml entity.name.function.cfml

    Function bar() {
//  ^^^^^^^^ meta.function.declaration.cfml storage.type.function.cfml
        IF (a) { RETURN 1; } ELSE IF (b) { BREAK; } ELSE { VAR x = TRUE; }
//      ^^ keyword.control.conditional.if.cfml
//               ^^^^^^ keyword.control.flow.return.cfml
//                           ^^^^^^^ keyword.control.conditional.elseif.cfml
//                                         ^^^^^ keyword.control.flow.break.cfml
//                                                  ^^^^ keyword.control.conditional.else.cfml
//                                                         ^^^ keyword.declaration.cfml
//                                                                 ^^^^ constant.language.boolean.true.cfml
        For (var i = 1; i < 2; i++) {}
//      ^^^ keyword.control.loop.for.cfml
        WHILE (a) {}
//      ^^^^^ keyword.control.loop.while.cfml
        Try {} Catch (any e) {} Finally {}
//      ^^^ keyword.control.exception.try.cfml
//             ^^^^^ keyword.control.exception.catch.cfml
//                              ^^^^^^^ keyword.control.exception.finally.cfml
        Switch (a) { Case 1: break; Default: break; }
//      ^^^^^^ keyword.control.conditional.switch.cfml
//                   ^^^^ keyword.control.conditional.case.cfml
//                                  ^^^^^^^ keyword.control.conditional.default.cfml
        o = New Foo();
//          ^^^ keyword.operator.word.new.cfml
//              ^^^ entity.name.class.cfml
        THROW "message";
//      ^^^^^ keyword.control.flow.throw.cfml
        n = NULL;
//          ^^^^ constant.language.null.cfml
    }
}
component {
    boolean public function isPackage() {}
//  ^^^^^^^ meta.function.declaration.cfml storage.type.primitive.cfml
//          ^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//                          ^^^^^^^^^ meta.function.declaration.cfml entity.name.function.cfml
    com.foo.Bar private static function make() {}
//  ^^^^^^^^^^^ meta.function.declaration.cfml storage.type.object.cfml
//              ^^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//                      ^^^^^^ meta.function.declaration.cfml storage.modifier.cfml
//                                      ^^^^ meta.function.declaration.cfml entity.name.function.cfml
}
component {
    function f() { g = (a) => a; }
//  ^^^^^^^^ storage.type.function.cfml keyword.declaration.function.cfml
//                         ^^ storage.type.function.arrow.cfml keyword.declaration.function.arrow.cfml
}
abstract component {
//       ^^^^^^^^^ meta.class.declaration.cfml storage.type.class.cfml keyword.declaration.class.cfml
}
