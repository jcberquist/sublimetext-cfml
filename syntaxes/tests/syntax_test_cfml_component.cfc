<!--- SYNTAX TEST "cfml.sublime-syntax" --->
<cfcomponent
<!--- <- embedding.cfml source.cfml meta.tag.cfml meta.class.cfml punctuation.definition.tag.begin.cfml --->
 <!--- <- embedding.cfml source.cfml meta.tag.cfml meta.class.cfml entity.name.tag.cfml storage.type.class.cfml --->
extends="base.test"
<!--- <- meta.class.inheritance.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml --->
<!---  ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml --->
<!---   ^ meta.class.inheritance.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml --->
<!---    ^ meta.class.inheritance.cfml string.quoted.double.cfml entity.other.inherited-class.cfml --->
<!---              ^ embedding.cfml source.cfml meta.tag.cfml meta.class.cfml --->
extends='base.test'
<!--- <- meta.class.inheritance.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml --->
<!---  ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml --->
<!---   ^ meta.class.inheritance.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml --->
<!---    ^ meta.class.inheritance.cfml string.quoted.single.cfml entity.other.inherited-class.cfml --->
<!---              ^ embedding.cfml source.cfml meta.tag.cfml meta.class.cfml --->
extends=base.test
<!--- <- meta.class.inheritance.cfml entity.other.attribute-name.cfml storage.modifier.extends.cfml --->
<!---  ^ meta.class.inheritance.cfml punctuation.separator.key-value.cfml --->
<!---   ^ meta.class.inheritance.cfml string.unquoted.cfml entity.other.inherited-class.cfml --->
<!---            ^ embedding.cfml source.cfml meta.tag.cfml meta.class.cfml --->
>
 <!--- <- meta.class.body.tag.cfml --->

  <cfproperty name="randomService">
  <!--- <- embedding.cfml source.cfml meta.tag.cfml meta.tag.property.cfml punctuation.definition.tag.begin.cfml --->
<!---               ^ embedding.cfml source.cfml meta.tag.cfml meta.tag.property.cfml string.quoted.double.cfml meta.tag.property.name.cfml --->
  <cffunction name="init">
  <!--- <- embedding.cfml source.cfml meta.tag.cfml meta.function.cfml punctuation.definition.tag.begin.cfml --->
   <!--- <- embedding.cfml source.cfml meta.tag.cfml meta.function.cfml entity.name.tag.cfml storage.type.function.cfml --->
<!---                    ^ embedding.cfml source.cfml meta.tag.cfml meta.function.cfml punctuation.definition.tag.end.cfml --->
<!---                     ^ meta.function.body.tag.cfml --->
    <cfreturn this>
  </cffunction>

  <cffunction name="testHtml" returntype="string" access="public">
<!---              ^ embedding.cfml source.cfml meta.tag.cfml meta.function.cfml -entity.name.function.cfml --->
<!---               ^ embedding.cfml source.cfml meta.tag.cfml meta.function.cfml entity.name.function.cfml --->
<!---                                     ^ embedding.cfml source.cfml meta.tag.cfml meta.function.cfml string.quoted.double.cfml storage.type.return-type.primitive.cfml --->
<!---                                                     ^ embedding.cfml source.cfml meta.tag.cfml meta.function.cfml string.quoted.double.cfml storage.modifier.cfml --->
    <cfargument name="argName" type="any">
    <!--- <- meta.tag.argument.cfml --->
    <cfsavecontent variable="testHtml">
      <div class="alert alert-<cfif danger>danger<cfelse>success</cfif>">Alert!</div>
<!---  ^ embedding.cfml source.cfml meta.tag.block.any.html entity.name.tag.block.any.html --->
<!---                          ^ embedding.cfml source.cfml meta.tag.block.any.html string.quoted.double.html meta.tag.cfml entity.name.tag.cfml --->
    </cfsavecontent>
  </cffunction>

</cfcomponent>
<!--- <- embedding.cfml source.cfml meta.tag.cfml punctuation.definition.tag.begin.cfml --->
