<!--- SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax" --->
<cfscript>
classInstance = java { public class class1 { } }
<!---                  ^^^^^^ meta.class.java storage.modifier.java --->

function test(int i) a="b" type="java" { return i*2; }
<!---                                  ^ meta.java.cfml --->
<!---                                    ^^^^^^ meta.statement.flow.return.java keyword.control.flow.return.java --->
</cfscript>

<cfjava handle="instance"> 
import java.io.*;  
public class Harmless { } </cfjava>
<!---  ^^^^^ meta.class.java keyword.declaration.class.java --->