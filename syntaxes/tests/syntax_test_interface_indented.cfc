// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
  // a banner comment
    interface extends="Base" {
//  ^^^^^^^^^ meta.interface.declaration.cfml keyword.declaration.interface.cfml
//                           ^ meta.interface.body.cfml punctuation.section.block.begin.cfml
        function f();
//               ^ meta.interface.body.cfml entity.name.function.cfml
    }
