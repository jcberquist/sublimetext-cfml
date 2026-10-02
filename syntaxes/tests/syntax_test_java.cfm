<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfscript>
classInstance = java { public class class1 { } }
<!---                  ^^^^^^ meta.block.java.cfml source.java.embedded.cfml meta.class.java storage.modifier.java --->
<!---                ^ meta.block.java.cfml punctuation.section.block.begin.cfml - source.java --->

function test(int i) a="b" type="java" { return i*2; }
<!---                                  ^ meta.java.cfml --->
<!---                                    ^^^^^^ meta.java.cfml source.java.embedded.cfml meta.statement.flow.return.java keyword.control.flow.return.java --->
<!---                                                ^ meta.java.cfml punctuation.section.block.end.cfml - source.java --->
</cfscript>

<cfjava handle="instance"> 
import java.io.*;  
public class Harmless { } </cfjava>
<!---  ^^^^^ meta.java.cfml source.java.embedded.cfml meta.class.java keyword.declaration.class.java --->