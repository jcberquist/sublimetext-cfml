<!--- SYNTAX TEST "cfml.sublime-syntax" --->
<div>
 <!--- <- embedding.cfml text.html.cfml meta.tag entity.name.tag --->
<cfset testArray = []>
 <!--- <- embedding.cfml entity.name.tag --->
<cfset arrayAppend(testArray, 1)>
<!---  ^ embedding.cfml meta.tag source.cfml.script meta.function-call.support.cfml support.function.cfml --->
<!---             ^ embedding.cfml meta.tag source.cfml.script meta.function-call.parameters.support.cfml punctuation.section.group.begin.cfml --->
</div>
<cfoutput>
<!---     ^ embedding.cfml text.html.cfml meta.scope.cfoutput.cfml text.html.cfml --->
#now()#
<!--- <- embedding.cfml text.html.cfml meta.scope.cfoutput.cfml text.html.cfml punctuation.definition.template-expression.begin.cfml --->
  <!--- <- embedding.cfml text.html.cfml meta.scope.cfoutput.cfml text.html.cfml source.cfml.script support.function.cfml --->
</cfoutput>

<cfquery name="test">
<!--- this should be a comment <cfqueryparam value=""> --->
<!---                           ^ embedding.cfml text.html.cfml meta.scope.cfquery.cfml source.sql comment.line.cfml --->
'unclosed sql string
</cfquery>
<!--- <- -source.sql --->
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
    <!--- <- meta.function-call.cfml meta.function-call.parameters.cfml entity.other.function-parameter.cfml --->
)>

<cfquery>SELECT * FROM #obj.property# WHERE s = '#obj.prop#'</cfquery>
<!---                       ^^^^^^^^ source.sql source.cfml.script meta.property.cfml --->
<!---                                                 ^^^^ source.sql source.cfml.script meta.property.cfml --->
<cfquery>BULK INSERT VAR1 FROM 'C:\#path#'</cfquery>
<!---                             ^ source.sql string.quoted.single.sql constant.character.escape.sql  --->
<!---                              ^ source.sql string.quoted.single.sql punctuation.definition.template-expression.begin.cfml --->
<cfscript>
foo = 'hello world';
<!--- <- embedding.cfml text.html.cfml source.cfml.script variable.other.readwrite.cfml --->
<!---  ^ embedding.cfml text.html.cfml source.cfml.script string.quoted.single.cfml --->
<!---              ^ embedding.cfml text.html.cfml source.cfml.script punctuation.terminator.statement.cfml --->

arrayAppend(foo, 10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.support.cfml support.function.cfml --->
<!---      ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.support.cfml meta.function-call.parameters.support.cfml punctuation.section.group.begin.cfml --->
<!---              ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.support.cfml meta.function-call.parameters.support.cfml punctuation.section.group.end.cfml --->
myArray.append(10);
<!---   ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.support.cfml support.function.member.cfml --->
<!---         ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.support.cfml meta.function-call.parameters.method.support.cfml punctuation.section.group.begin.cfml --->
myFunc();
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.parameters.cfml punctuation.section.group.begin.cfml --->
myFunc(10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.parameters.cfml punctuation.section.group.begin.cfml --->
myObj.addVal(10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script variable.other.object.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml --->
<!---       ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml meta.function-call.parameters.method.cfml punctuation.section.group.begin.cfml --->
myFunc().addVal(10);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.parameters.cfml punctuation.section.group.begin.cfml --->
<!---    ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml --->
<!---          ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.method.cfml meta.function-call.parameters.method.cfml punctuation.section.group.begin.cfml --->
</cfscript>
