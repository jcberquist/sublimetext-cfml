// SYNTAX TEST "Packages/CFML/syntaxes/cfml.sublime-syntax"
abstract component {
// <- embedding.cfml source.cfml.script meta.class.declaration.cfml storage.modifier.cfml

  static {
//^ meta.block.static.cfml keyword.control.static.cfml
    staticValue = 5;
  }

  private final numeric function testStatic(){
    return static.staticValue;
//         ^ variable.language.scope.cfml
  }


    abstract function getFile();
//  ^ storage.modifier.cfml
    final function getDirectory() {
//  ^ storage.modifier.cfml
        return getDirectoryFromPath(getFile());
    }

    function test() {
      test.class::staticMethod();
//    ^^^^^^^^^^ entity.name.class.cfml
//              ^^ punctuation.accessor.static.cfml
//                ^^^^^^^^^^^^ meta.function-call.method.static.cfml variable.function.static.cfml
      test.class::staticVal;
//    ^^^^^^^^^^ entity.name.class.cfml
//              ^^ punctuation.accessor.static.cfml
//                ^^^^^^^^^ meta.property.cfml
    }
}
