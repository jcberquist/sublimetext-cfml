<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfscript>
var [ a, b ] = [ 1, 2 ];
    <!--- <- meta.binding.destructuring.sequence.cfml punctuation.section.sequence.begin.cfml --->
[ a, b ] = [ 1, 2 ];
<!--- <- text.html.cfml source.cfml.script meta.sequence.cfml punctuation.section.sequence.begin.cfml --->

var { a, b } = { a: 1, b: 2 };
    <!--- <- meta.binding.destructuring.mapping.cfml punctuation.section.mapping.begin.cfml --->
<!--- ^ meta.binding.destructuring.mapping.cfml meta.struct-literal.key.cfml meta.binding.name.cfml variable.other.readwrite.cfml --->
({ a, b } = { a: 1, b: 2 });
 <!--- <- meta.struct-literal.cfml punctuation.section.mapping.begin.cfml --->
<!--- ^ meta.struct-literal.cfml variable.other.readwrite.cfml --->
</cfscript>