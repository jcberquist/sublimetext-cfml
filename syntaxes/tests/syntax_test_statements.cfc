// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f() {
        Service::get();
//      ^^^^^^^ entity.name.class.cfml -entity.name.label
//             ^^ punctuation.accessor.static.cfml
//               ^^^ meta.function-call.method.static.cfml variable.function.static.cfml
        outer: for (i = 1; i < 2; i++) {}
//      ^^^^^ entity.name.label.cfml
//           ^ punctuation.separator.cfml
        try {} catch ("java.lang.Exception" e) {}
//                    ^ punctuation.definition.string.begin.cfml
//                    ^^^^^^^^^^^^^^^^^^^^^ support.type.exception.cfml
//                                        ^ punctuation.definition.string.end.cfml
//                                          ^ variable.other.readwrite.cfml
        try {} catch ('TestBox.SkipSpec' var e) {}
//                    ^^^^^^^^^^^^^^^^^^ support.type.exception.cfml
//                                       ^^^ storage.type.cfml
//                                           ^ variable.other.readwrite.cfml
        try {} catch (java.lang.Exception e) {}
//                    ^^^^^^^^^^^^^^^^^^^ support.type.exception.cfml
//                                        ^ variable.other.readwrite.cfml
        o = new "com.foo"(1);
//          ^^^^^^^^^^^^^^^^ meta.instance.constructor.cfml
//              ^^^^^^^^^ string.quoted.double.cfml
//                       ^^^ meta.function-call.arguments.method.cfml meta.group.cfml
        o = new '#path#'(a = b);
//          ^^^^^^^^^^^^^^^^^^^ meta.instance.constructor.cfml
//                ^^^^ source.cfml.script variable.other.readwrite.cfml
//                       ^ entity.other.method-parameter.cfml
        x = default; var default = 1; y = a.default;
//          ^^^^^^^ variable.other.readwrite.cfml
//                       ^^^^^^^ meta.binding.name.cfml variable.other.readwrite.cfml
//                                          ^^^^^^^ meta.property.cfml
        switch (x) { case 1: default = 1; break; default : break; }
//                           ^^^^^^^ variable.other.readwrite.cfml
//                                               ^^^^^^^ keyword.control.conditional.default.cfml
//                                                       ^ punctuation.separator.cfml
        a.b.1234 = form.1;
//          ^^^^ meta.property.cfml -constant.numeric
//                      ^ meta.property.cfml -constant.numeric
        n = a.b + .5;
//                ^^ constant.numeric.value.cfml
        if (x) {} elseif (y) {} else {}
//                ^^^^^^ meta.conditional.cfml keyword.control.conditional.elseif.cfml
//                        ^ meta.conditional.cfml meta.group.cfml variable.other.readwrite.cfml
        try {} catch (local.exp) {}
//                    ^^^^^^^^^ variable.other.readwrite.cfml
//                             ^ punctuation.section.group.end.cfml
        try {} catch (any local.exp) {}
//                    ^^^ support.type.exception.cfml
//                        ^^^^^^^^^ variable.other.readwrite.cfml
        f($a = 1, b = 2);
//        ^^ entity.other.function-parameter.cfml
//                ^ entity.other.function-parameter.cfml
        o.m($a = 1);
//          ^^ entity.other.method-parameter.cfml
        y = IsNull (x);
//          ^^^^^^ meta.function-call.support.cfml support.function.cfml
        z = s.len ();
//            ^^^ meta.function-call.method.support.cfml support.function.member.cfml
        while ((var line = r.readLine()) != -1) {}
//              ^^^ meta.group.cfml meta.group.cfml keyword.declaration.cfml
//                  ^^^^ variable.other.readwrite.cfml
//                         ^ variable.other.object.cfml
    }
}
component {
    function f() {
        q = query('a':[1], "b": [2]);
//                ^^^ meta.function-call.arguments.support.cfml string.quoted.single.cfml
//                   ^ meta.function-call.arguments.support.cfml punctuation.separator.key-value.cfml
//                    ^ meta.sequence.cfml punctuation.section.sequence.begin.cfml
//                         ^^^ string.quoted.double.cfml
//                            ^ punctuation.separator.key-value.cfml
        x = f("a" & b, c ? "d" : e);
//            ^^^ string.quoted.double.cfml
//                             ^ keyword.operator.ternary.cfml
    }
}
component {
    function f() {
        x = a.b.MAX_SIZE + form.1;
//            ^ meta.property.cfml variable.other.member.cfml
//              ^^^^^^^^ meta.property.constant.cfml variable.other.member.cfml
//                              ^ meta.property.cfml variable.other.member.cfml
    }
}
