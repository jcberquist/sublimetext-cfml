// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f() {
        s = {a: 1, "b": 2, c = 3};
//          ^ meta.struct-literal.cfml meta.mapping.cfml punctuation.section.mapping.begin.cfml
//           ^ meta.mapping.cfml meta.struct-literal.key.cfml meta.mapping.key.cfml
//                 ^^^ meta.mapping.key.cfml string.quoted.double.cfml
//                 ^^^ meta.mapping.key string - meta.mapping.key meta meta
//                      ^ meta.mapping.cfml - meta.mapping.key
//                         ^ meta.mapping.key.cfml
        r = [a: 1, 'b': 2];
//          ^ meta.mapping.cfml punctuation.section.mapping.begin.cfml
//           ^ meta.mapping.key.cfml
//                 ^^^ meta.mapping.key string - meta.mapping.key meta meta
        o = { "m": function() {} };
//             ^ meta.mapping.key.cfml entity.name.function.cfml
    }
}
