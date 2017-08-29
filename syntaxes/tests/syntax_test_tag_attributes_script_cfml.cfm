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
param name = "test" default = now() * then;
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.other.attribute-name.cfml --->
<!---                         ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml support.function.cfml --->
<!---                                 ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml variable.other.readwrite.cfml --->
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
<!---            ^ embedding.cfml text.html.cfml source.cfml.script meta.block.cfml punctuation.section.block.begin.cfml - meta.tag.script.cfml --->
}

thread action="run" name="threadName" {
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cfml entity.name.tag.script.cfml --->
<!--- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.tag.script.cfml  --->

  thread.varName = "test";
  <!--- <- embedding.cfml text.html.cfml source.cfml.script meta.block.cfml variable.language.scope.cfml --->
}

cfhttp( url = "www.google.com" ) {
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cf.cfml entity.name.tag.script.cfml  --->
<!---   ^ embedding.cfml text.html.cfml source.cfml.script meta.tag.script.cf.cfml entity.other.attribute-name.cfml  --->

}

cfcExists( someArg = 1 );
<!--- <- embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml variable.function.cfml  --->
<!---      ^ embedding.cfml text.html.cfml source.cfml.script meta.function-call.cfml meta.function-call.parameters.cfml entity.other.function-parameter.cfml  --->
</cfscript>
