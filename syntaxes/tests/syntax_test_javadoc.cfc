// SYNTAX TEST "Packages/CFML/syntaxes/cfml.sublime-syntax"
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
