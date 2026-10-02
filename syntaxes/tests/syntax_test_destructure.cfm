<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfscript>
var [ a, b ] = [ 1, 2 ];
    <!--- <- meta.binding.destructuring.sequence.cfml punctuation.section.sequence.begin.cfml --->
[ a, b ] = [ 1, 2 ];
<!--- <- text.html.cfml source.cfml.script meta.sequence.cfml punctuation.section.sequence.begin.cfml --->

var { a, b } = { a: 1, b: 2 };
    <!--- <- meta.binding.destructuring.mapping.cfml punctuation.section.mapping.begin.cfml --->
<!--- ^ meta.binding.destructuring.mapping.cfml meta.mapping.key.cfml meta.binding.name.cfml variable.other.readwrite.cfml --->
({ a, b } = { a: 1, b: 2 });
 <!--- <- meta.mapping.cfml punctuation.section.mapping.begin.cfml --->
<!--- ^ meta.mapping.cfml variable.other.readwrite.cfml --->

final [ fa, fb ] = x;
<!--- ^ meta.binding.destructuring.sequence.cfml punctuation.section.sequence.begin.cfml --->
<!---       ^^ meta.binding.destructuring.sequence.cfml meta.binding.name.cfml variable.other.readwrite.cfml --->
final { fc, fd: fe } = s;
<!--- ^ meta.binding.destructuring.mapping.cfml punctuation.section.mapping.begin.cfml - meta.block --->
<!---       ^^ meta.binding.destructuring.mapping.cfml meta.mapping.key.cfml --->
<!---           ^^ meta.binding.destructuring.mapping.cfml meta.binding.name.cfml variable.other.readwrite.cfml --->
<!---                ^ keyword.operator.assignment.cfml - meta.binding --->

function f({ a, b: { c }, "k": [ m ], ...r } = {}, d) {}
<!---      ^ meta.function.parameters.cfml meta.binding.destructuring.mapping.cfml punctuation.section.mapping.begin.cfml --->
<!---        ^ meta.binding.destructuring.mapping.cfml meta.binding.name.cfml variable.parameter.function.cfml --->
<!---           ^ meta.binding.destructuring.mapping.cfml meta.mapping.key.cfml - variable --->
<!---                ^ meta.binding.destructuring.mapping.cfml meta.binding.destructuring.mapping.cfml variable.parameter.function.cfml --->
<!---                            ^ meta.binding.destructuring.sequence.cfml variable.parameter.function.cfml --->
<!---                                 ^^^ meta.binding.destructuring.mapping.cfml keyword.operator.spread.cfml --->
<!---                                    ^ meta.binding.destructuring.mapping.cfml variable.parameter.function.cfml --->
<!---                                      ^ meta.binding.destructuring.mapping.cfml punctuation.section.mapping.end.cfml - invalid --->
<!---                                        ^ meta.function.parameters.cfml meta.parameter.optional.cfml keyword.operator.assignment.cfml --->
<!---                                              ^ meta.function.parameters.cfml variable.parameter.function.cfml - meta.binding --->
<!---                                                 ^ meta.function.body.cfml punctuation.section.block.begin.cfml --->
g = function({ k, v = {} }) { return k; };
<!---          ^ meta.binding.destructuring.mapping.cfml variable.parameter.function.cfml --->
<!---                 ^ meta.binding.destructuring.mapping.cfml meta.mapping.cfml punctuation.section.mapping.begin.cfml --->
<!---                    ^ meta.binding.destructuring.mapping.cfml punctuation.section.mapping.end.cfml --->
<!---                       ^ meta.function.body.cfml punctuation.section.block.begin.cfml --->
sum = ({ a, b }) => a + b;
<!---  ^ meta.function.parameters.cfml meta.binding.destructuring.mapping.cfml punctuation.section.mapping.begin.cfml --->
<!---       ^ meta.binding.destructuring.mapping.cfml variable.parameter.function.cfml --->
<!---            ^^ keyword.declaration.function.arrow.cfml --->
</cfscript>