// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
// <- source.cfml.script meta.class.declaration.cfml storage.type.class.cfml
}

component name="Sub" {  
// <- source.cfml.script meta.class.declaration.cfml storage.type.class.cfml
    function t() {
        var inline=new component {  
//                 ^^^ meta.instance.constructor.cfml keyword.operator.word.new.cfml
//                     ^^^^^^^^^ meta.instance.constructor.cfml storage.type.class.cfml
        };  
    }
}