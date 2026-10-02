// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
// <- source.cfml.script meta.class.declaration.cfml keyword.declaration.class.cfml
}

component name="Sub" {  
// <- source.cfml.script meta.class.declaration.cfml keyword.declaration.class.cfml
    function t() {
        var inline=new component {  
//                 ^^^ meta.instance.constructor.cfml keyword.operator.word.new.cfml
//                     ^^^^^^^^^ meta.instance.constructor.cfml storage.type.class.cfml
//                               ^ meta.class.body.cfml punctuation.section.block.begin.cfml - meta.instance - meta.block
        };  
//      ^ meta.class.body.cfml punctuation.section.block.end.cfml
//       ^ punctuation.terminator.statement.cfml - punctuation.terminator.statement.empty
        var b = new Component extends="Base" accessors=true hint="#x("y")#" {
//                            ^^^^^^^ meta.instance.constructor.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml
//                                     ^^^^ meta.instance.constructor.cfml entity.other.inherited-class.cfml
//                                           ^^^^^^^^^ meta.instance.constructor.cfml entity.other.attribute-name.cfml - variable
//                                                     ^^^^ meta.instance.constructor.cfml string.unquoted.cfml
//                                                                 ^ meta.instance.constructor.cfml meta.interpolation.cfml variable.function.cfml
//                                                                          ^ meta.class.body.cfml punctuation.section.block.begin.cfml - meta.instance
            function g() { return 1; }
//          ^^^^^^^^ meta.class.body.cfml meta.class.body.cfml meta.function.declaration.cfml keyword.declaration.function.cfml
        };
//      ^ meta.class.body.cfml punctuation.section.block.end.cfml
        var m = new component
            accessors=true // note
//          ^^^^^^^^^ meta.instance.constructor.cfml entity.other.attribute-name.cfml
//                         ^^^^^^^ comment.line.double-slash.cfml
        {
//      ^ meta.class.body.cfml punctuation.section.block.begin.cfml - meta.instance
        };
//      ^ meta.class.body.cfml punctuation.section.block.end.cfml
        var n = new component(1);
//                           ^ meta.instance.constructor.cfml meta.function-call.arguments.method.cfml
        var o = new component
            (1);
//          ^ meta.instance.constructor.cfml meta.function-call.arguments.method.cfml - invalid
        if (isNull(new Component())) { return 1; }
//                                   ^ meta.conditional.cfml meta.block.cfml punctuation.section.block.begin.cfml
        var c = x ?: new component {};
//                                 ^ meta.class.body.cfml punctuation.section.block.begin.cfml
        var d = new Component() + 1;
//                  ^^^^^^^^^ meta.instance.constructor.cfml storage.type.class.cfml
//                              ^ keyword.operator.arithmetic.cfml - meta.instance
        var e = new component.path.Thing();
//                  ^^^^^^^^^^^^^^^^^^^^ meta.instance.constructor.cfml entity.name.class.cfml - storage
    }
}