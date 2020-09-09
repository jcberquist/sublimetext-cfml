<!--- SYNTAX TEST "Packages/CFML/syntaxes/cfml.sublime-syntax" --->
<cfscript>
thisQuery = queryExecute("SELECT * from myTable WHERE myColumn = 1", "SELECT * from myTable WHERE myColumn = 1");
<!---                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
<!---                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
thisQuery = queryExecute(params = {}, sql = "SELECT * FROM myTable");
<!---                                        ^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
var test = "FROM myTable WHERE test = '#obj.property#'"
<!---       ^^^^ meta.string.quoted.double.cfml source.sql keyword.other.DML.sql --->
<!---                                       ^^^^^^^^ source.cfml.script source.sql source.cfml.script meta.property.cfml --->

sql = "select *";
<!---  ^^^^^^^^ source.sql -string.quoted.double.cfml --->
sql = "
      select
<!--- ^^^^^^ source.sql -string.quoted.double.cfml --->
";
sql = "
      select top(2)
<!--- ^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
";
sql = "select a.b.c from";
<!---  ^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
sql = "select a.b.c,";
<!---  ^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
sql = "select a.b.c as columnAlias,";
<!---  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
sql = "from
<!---  ^^^^ source.sql -string.quoted.double.cfml --->
";
sql = "from table q
<!---  ^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
";
sql = "where
<!---  ^^^^^ source.sql -string.quoted.double.cfml --->
";
sql = "where a.b = 'astring'";
<!---  ^^^^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->

sql = "group by a.b,
<!---  ^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->
";
sql = "inner join a.table";
<!---  ^^^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->

sql = "left outer join "
<!---  ^^^^^^^^^^^^^^^^ source.sql -string.quoted.double.cfml --->



not_sql = "select a.b.c";
<!---      ^^^^^^^^^^^^ string.quoted.double.cfml -source.sql --->
not_sql = "from table q";
<!---      ^^^^^^^^^^^^ string.quoted.double.cfml -source.sql --->
not_sql = "group by a.b";
<!---      ^^^^^^^^^^^^ string.quoted.double.cfml -source.sql --->
</cfscript>
