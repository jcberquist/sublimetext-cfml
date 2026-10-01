// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
/**
This is a description of the component
// <- embedding.cfml source.cfml.script comment.block.documentation.cfml text.html
//                                    ^ -text.html
* @attribute and some hint text
// <- embedding.cfml source.cfml.script comment.block.documentation.cfml
  // <- keyword.other.documentation.cfml punctuation.definition.keyword.cfml
// ^ -punctuation.definition.keyword.cfml
//          ^ -keyword.other.documentation.cfml
//           ^ text.html
//                             ^ -text.html
@another.attribute and some hint text
// <- embedding.cfml source.cfml.script comment.block.documentation.cfml keyword.other.documentation.cfml punctuation.definition.keyword.cfml
 // <- -punctuation.definition.keyword.cfml
//                ^ -keyword.other.documentation.cfml
//                 ^ text.html
//                                   ^ -text.html
*/
component {

    /**/ a;
//       ^ source.cfml.script variable.other.readwrite.cfml - comment

}
component {
    /* block */
//  ^^ comment.block.cfml punctuation.definition.comment.begin.cfml
//           ^^ comment.block.cfml punctuation.definition.comment.end.cfml
    /** doc */
//  ^^^ comment.block.documentation.cfml punctuation.definition.comment.begin.cfml
//          ^^ comment.block.documentation.cfml punctuation.definition.comment.end.cfml
    <!--- tag --->
//  ^^^^^ comment.block.cfml punctuation.definition.comment.begin.cfml
//            ^^^^ comment.block.cfml punctuation.definition.comment.end.cfml
    // line
//  ^^ comment.line.double-slash.cfml punctuation.definition.comment.cfml
}
component {
    /**
     * Returns a Map<Boolean, List<String>> where a <> 5.
//                  ^ comment.block.documentation.cfml - invalid
//                                ^ comment.block.documentation.cfml - invalid
//                                                  ^^ comment.block.documentation.cfml - invalid
     * @param x the <b>value</b>
//                   ^ comment.block.documentation.cfml meta.tag.inline.any.html entity.name.tag.inline.any.html
     * "><img src=x onerror=alert(1)
     */
//   ^^ comment.block.documentation.cfml punctuation.definition.comment.end.cfml
    function f(x) {}
//           ^ meta.function.declaration.cfml entity.name.function.cfml
}
