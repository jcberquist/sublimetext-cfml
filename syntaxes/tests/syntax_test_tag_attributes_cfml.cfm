<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
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
<!---       ^ punctuation.section.interpolation.begin.cfml --->
<!---        ^ variable.other.readwrite.cfml --->

<input <cfif a>checked<cfelse>disabled</cfif> value="#v#">
<!---          ^^^^^^^ meta.tag.inline.form.html entity.other.attribute-name.html --->
<!---                 ^ meta.tag.inline.form.html meta.tag.cfml punctuation.definition.tag.begin.cfml - entity.other.attribute-name - meta.attribute-with-value --->
<!---                         ^^^^^^^^ meta.tag.inline.form.html entity.other.attribute-name.html --->
<!---                                 ^^ meta.tag.inline.form.html meta.tag.cfml punctuation.definition.tag.begin.cfml - entity.other.attribute-name - meta.attribute-with-value --->
<!---                                         ^^^^^ meta.tag.inline.form.html entity.other.attribute-name.html --->
