// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f() {
        query
//      ^^^^^ variable.other -entity.name.tag -meta.tag
            .where(1)
//          ^ punctuation.accessor.cfml
//           ^^^^^ meta.function-call.method.cfml variable.function.cfml
            .where(2);
//                   ^ punctuation.terminator.statement.cfml
        x = 1;
//      ^ variable.other.readwrite.cfml
        transaction {
//      ^^^^^^^^^^^ meta.tag.script.cfml entity.name.tag.script.cfml
            x = 1;
//          ^ meta.block.cfml variable.other.readwrite.cfml
        }
        y = 2;
//      ^ variable.other.readwrite.cfml -meta.tag
        lock name="a" timeout=1 {
//      ^^^^ meta.tag.script.cfml entity.name.tag.script.cfml
            x = 1;
        }
        http
//      ^^^^ meta.tag.script.cfml entity.name.tag.script.cfml
            url="x";
//          ^^^ meta.tag.script.cfml entity.other.attribute-name.cfml
//                 ^ punctuation.terminator.statement.cfml -meta.tag
        setting enablecfoutputonly=true;
//                                     ^ punctuation.terminator.statement.cfml -meta.tag
        z = 3;
//      ^ variable.other.readwrite.cfml
        cfhttp url="x" result="r";
//      ^^^^^^ meta.tag.script.cfml entity.name.tag.script.cfml
//             ^^^ meta.tag.script.cfml entity.other.attribute-name.cfml
        cfinvoke
//      ^^^^^^^^ meta.tag.script.cfml entity.name.tag.script.cfml
            component = "#arguments.component#"
//          ^^^^^^^^^ meta.tag.script.cfml entity.other.attribute-name.cfml -storage
            method = "go";
//          ^^^^^^ meta.tag.script.cfml entity.other.attribute-name.cfml
        cfquery
//      ^^^^^^^ variable.other -meta.tag
            .where(1);
//           ^^^^^ variable.function.cfml
        cffile (action="write" file="#path#" output="x");
//      ^^^^^^ meta.tag.script.cf.cfml entity.name.tag.script.cfml
//              ^^^^^^ meta.tag.script.cf.attributes.cfml entity.other.attribute-name.cfml
        cfdocument (format="PDF", name="local.test") {
//      ^^^^^^^^^^ meta.tag.script.cf.cfml entity.name.tag.script.cfml
            echo("x");
        }
    }
}
component {
    function g() {
        cfhttp(url="x");
//                     ^ punctuation.terminator.statement.cfml - punctuation.terminator.statement.empty - meta.tag
        cfdocument (format="PDF") { x = 1; }
//                                ^ meta.block.cfml punctuation.section.block.begin.cfml
        y = 2;
//      ^ variable.other.readwrite.cfml - meta.tag
    }
}
