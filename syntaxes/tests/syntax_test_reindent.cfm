<!--- SYNTAX TEST reindent "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfoutput>
    <cfif a>
        <div>
            #x#
        </div>
    <cfelseif b>
        <cfset y = 1>
    <cfelse>
        <cfloop from="1" to="2" index="i">
            <p>#i#</p>
        </cfloop>
    </cfif>
    <cfscript>
        if (a) {
            b = 1;
        }
    </cfscript>
</cfoutput>
