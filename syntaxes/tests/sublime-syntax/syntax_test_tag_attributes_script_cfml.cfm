<!--- SYNTAX TEST "cfml.sublime-syntax" --->
<cfscript>
param NAME="testVar";
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---       ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.quoted.double.cfml --->
param name = "test" default = "#now()#";
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---         ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.quoted.double.cfml --->
param name = "test" default = (now() * then);
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---                          ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml support.function.cfml --->
<!---                                  ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml variable.other.cfml --->
param name = "test" default = now() then;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---                         ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml support.function.cfml --->
<!---                               ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
param name = "test"
default = now() then;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---     ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml support.function.cfml --->
<!---           ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
param testVar;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
param foo testVar;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml storage.type.cfml --->
<!---     ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
param numeric testVar = 321;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml storage.type.cfml --->
<!---         ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
<!---                   ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml constant.numeric.cfml --->
param testVar default = "hello";
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
<!---         ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---                    ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.quoted.double.cfml --->
param numeric testVar default="321";
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml storage.type.cfml --->
<!---         ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
<!---                 ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
param testVar="hello";
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
<!---          ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.quoted.double.cfml --->
param rc.testVar = 100;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
<!---    ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml string.unquoted.cfml --->
<!---              ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml constant.numeric.cfml --->
  param integer testVar = 100;
<!--- <- embedding.cfml text.html.cfml source.cfml.script - meta.tag.script.cfml --->

transaction {
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
}

lock timeout="30"{
<!---            ^ embedding.cfml text.html.cfml source.cfml.script meta.group.braces.curly meta.brace.curly.cfml - meta.tag.script.cfml --->
}

thread action="run" name="threadName" {
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->

  thread.varName = "test";
  <!--- <- embedding.cfml text.html.cfml source.cfml.script meta.group.braces.curly variable.language.scope.cfml --->
}

cfhttp( url = "www.google.com" );
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cf.cfml entity.name.tag.script.cfml  --->
<!---   ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cf.cfml entity.other.attribute-name.cfml  --->

</cfscript>