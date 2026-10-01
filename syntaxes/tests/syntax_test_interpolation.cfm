<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfoutput>text #x.y# and ## done</cfoutput>
<!---          ^ meta.interpolation.cfml punctuation.section.interpolation.begin.cfml --->
<!---           ^ meta.interpolation.cfml source.cfml.script variable.other.object.cfml - source.cfml.script source.cfml.script --->
<!---              ^ meta.interpolation.cfml punctuation.section.interpolation.end.cfml --->
<!---                    ^^ constant.character.escape.hash.cfml - meta.interpolation --->
<cfloop from="1" to="#n#" index="i"></cfloop>
<!---                ^ meta.string.quoted.double.cfml meta.interpolation.cfml punctuation.section.interpolation.begin.cfml - string.quoted --->
<!---                 ^ meta.interpolation.cfml source.cfml.script variable.other.readwrite.cfml - string.quoted --->
<cfset s = "a#b#c">
<!---       ^ meta.string.quoted.double.cfml string.quoted.double.cfml --->
<!---         ^ meta.string.quoted.double.cfml meta.interpolation.cfml source.cfml.script variable.other.readwrite.cfml - string.quoted --->
<!---           ^ meta.string.quoted.double.cfml string.quoted.double.cfml - meta.interpolation --->
<cfquery name="q">select * from t where id = #id#</cfquery>
<!---                                        ^^^^ meta.interpolation.cfml --->
<!---                                         ^^ source.cfml.script variable.other.readwrite.cfml --->
