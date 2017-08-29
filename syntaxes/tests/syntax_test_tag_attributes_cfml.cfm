<!--- SYNTAX TEST "cfml.sublime-syntax" --->
<cfparam name="test" type="string" default="hello">
<!---    ^ embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->
<!---        ^ embedding.cfml meta.tag.cfml punctuation.separator.key-value.cfml --->
<!---          ^ embedding.cfml meta.tag.cfml string.quoted.double.cfml --->

<cfparam name = "test" type = "string" default = "hello">
<!---    ^ embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->
<!---         ^ embedding.cfml meta.tag.cfml punctuation.separator.key-value.cfml --->
<!---            ^ embedding.cfml meta.tag.cfml string.quoted.double.cfml --->

<cfparam name = test default = now()>
<!---    ^ embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->
<!---         ^ embedding.cfml meta.tag.cfml punctuation.separator.key-value.cfml --->
<!---           ^ embedding.cfml meta.tag.cfml string.unquoted.cfml --->
<!---                ^ embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->
<!---                          ^ embedding.cfml meta.tag.cfml string.unquoted.cfml --->

<cfparam name = "test" novalueattribute>
<!---    ^ embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->
<!---         ^ embedding.cfml meta.tag.cfml punctuation.separator.key-value.cfml --->
<!---           ^ embedding.cfml meta.tag.cfml string.quoted.double.cfml --->
<!---                  ^ embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->

<cfparam name = "test"
<!---           ^ embedding.cfml meta.tag.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml --->
type = "string" default = "hello">
<!--- <- embedding.cfml meta.tag.cfml entity.other.attribute-name.cfml --->

<cfparam name =
"test" type = "string" default = "hello">
<!---  <- embedding.cfml meta.tag.cfml string.quoted.double.cfml --->

<cfparam name
= "test" type = "string" default = "hello">
<!--- <- embedding.cfml meta.tag.cfml punctuation.separator.key-value.cfml --->
   <!---  <- embedding.cfml meta.tag.cfml string.quoted.double.cfml --->

<cfhttp url=#some_url_var#>
<!---       ^ punctuation.definition.template-expression.begin.cfml --->
<!---        ^ variable.other.readwrite.cfml --->
