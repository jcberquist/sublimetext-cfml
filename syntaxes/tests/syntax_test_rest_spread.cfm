<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfscript>
a = {...b};
<!---^^^ keyword.operator.spread.cfml --->
a = [...b];
<!---^^^ keyword.operator.spread.cfml --->

function test(a, ...rest) {
<!---            ^^^ meta.function.parameters.cfml keyword.operator.rest.cfml --->
}
</cfscript>