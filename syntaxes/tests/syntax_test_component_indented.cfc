// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
    component extends="Base" {
//  ^^^^^^^^^ meta.class.declaration.cfml keyword.declaration.class.cfml
//            ^^^^^^^ meta.class.declaration.cfml meta.class.inheritance.cfml
//                           ^ meta.class.body.cfml punctuation.section.block.begin.cfml

        function f() {
//               ^ meta.class.body.cfml entity.name.function.cfml
            component = createObject( "component", "x" );
//          ^^^^^^^^^ variable.other.readwrite.cfml - keyword
            component.init();
//          ^^^^^^^^^ variable.other.object.cfml - keyword
            component[ "x" ] = 1;
//          ^^^^^^^^^ - keyword
            interface = 2;
//          ^^^^^^^^^ variable.other.readwrite.cfml - keyword
        }

    }

    /* a sub component */
    final component name="Sub" {
//  ^^^^^ meta.class.declaration.cfml storage.modifier.cfml
//        ^^^^^^^^^ meta.class.declaration.cfml keyword.declaration.class.cfml
//                             ^ meta.class.body.cfml
    }

    abstract /* base */ component
//  ^^^^^^^^ storage.modifier.cfml
//                      ^^^^^^^^^ meta.class.declaration.cfml keyword.declaration.class.cfml
    {
//  ^ meta.class.body.cfml punctuation.section.block.begin.cfml
    }
