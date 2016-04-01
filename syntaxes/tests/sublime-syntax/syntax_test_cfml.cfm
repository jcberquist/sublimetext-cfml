<!--- SYNTAX TEST "cfml.sublime-syntax" --->
<div>
 <!--- <- embedding.cfml text.html.cfml meta.tag entity.name.tag --->
<cfset testArray = []>
 <!--- <- embedding.cfml entity.name.tag --->
<cfset arrayAppend(testArray, 1)>
<!---  ^ embedding.cfml meta.tag source.cfml.script meta.support.function-call.cfml support.function.cfml --->
<!---             ^ embedding.cfml meta.tag source.cfml.script meta.support.function-call.arguments.cfml meta.brace.round.cfml --->
</div>
<cfoutput>
<!---     ^ embedding.cfml text.html.cfml meta.scope.cfoutput.cfml text.html.cfml --->
#now()#
<!--- <- embedding.cfml text.html.cfml meta.scope.cfoutput.cfml text.html.cfml constant.character.hash.cfml.start --->
  <!--- <- embedding.cfml text.html.cfml meta.scope.cfoutput.cfml text.html.cfml source.cfml.script support.function.cfml --->
</cfoutput>

<cfquery name="test">
<!--- this should be a comment <cfqueryparam value=""> --->
<!---                           ^ embedding.cfml text.html.cfml meta.scope.cfquery.cfml source.sql comment.line.cfml --->
</cfquery>

<cf_custom attrname="#test#">
<!--- <- meta.tag.custom.cfml --->
 <!--- <- meta.tag.custom.cfml entity.name.tag.custom.cfml --->
<!---      ^ meta.tag.custom.cfml entity.other.attribute-name.cfml --->
<!---                 ^ meta.tag.custom.cfml variable.other.readwrite.cfml --->
</cf_custom>
<!--- <- meta.tag.custom.cfml --->
  <!--- <- meta.tag.custom.cfml entity.name.tag.custom.cfml --->

<prefix:tag attrname="#test#">
<!--- <- meta.tag.custom.cfml --->
 <!--- <- meta.tag.custom.cfml entity.name.tag.custom.cfml --->
<!---  ^ meta.tag.custom.cfml entity.name.tag.custom.cfml punctuation.separator.prefix.cfml --->
<!---   ^ meta.tag.custom.cfml entity.name.tag.custom.cfml --->
<!---       ^ meta.tag.custom.cfml entity.other.attribute-name.cfml --->
<!---                  ^ meta.tag.custom.cfml variable.other.readwrite.cfml --->
</prefix:tag>
<!--- <- meta.tag.custom.cfml --->
  <!--- <- meta.tag.custom.cfml entity.name.tag.custom.cfml --->

<cfif col eq 1>
<!--- ^ meta.tag.cfml source.cfml.script variable.other.readwrite.cfml --->

<cfset f.result = componentCall(
    component="#f.componentName#",
    <!--- <- meta.function-call.cfml meta.function-call.arguments.cfml entity.other.function-parameter.cfml --->
)>

<cfscript>
foo = 'hello world';
<!--- <- embedding.cfml text.html.cfml source.cfml.script variable.other.readwrite.cfml --->
<!---  ^ embedding.cfml text.html.cfml source.cfml.script string.quoted.single.cfml --->
<!---              ^ embedding.cfml text.html.cfml source.cfml.script punctuation.terminator.statement.cfml --->

arrayAppend(foo, 10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.support.function-call.cfml support.function.cfml --->
<!---      ^ embedding.cfml text.html.cfml source.cfml.script meta.support.function-call.cfml meta.support.function-call.arguments.cfml meta.brace.round.cfml --->
<!---              ^ embedding.cfml text.html.cfml source.cfml.script meta.support.function-call.cfml meta.support.function-call.arguments.cfml meta.brace.round.cfml --->
myArray.append(10);
<!---   ^ embedding.cfml text.html.cfml source.cfml.script meta.support.function-call.member.cfml support.function.member.cfml --->
<!---         ^ embedding.cfml text.html.cfml source.cfml.script meta.support.function-call.member.cfml meta.support.function-call.member.arguments.cfml meta.brace.round.cfml --->
myFunc();
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.arguments.cfml meta.brace.round.cfml --->
myFunc(10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.arguments.cfml meta.brace.round.cfml --->
myObj.addVal(10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script variable.other.object.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml --->
<!---       ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml meta.function-call.method.arguments.cfml meta.brace.round.cfml --->
myFunc().addVal(10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.arguments.cfml meta.brace.round.cfml --->
<!---    ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml --->
<!---          ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml meta.function-call.method.arguments.cfml meta.brace.round.cfml --->
</cfscript>