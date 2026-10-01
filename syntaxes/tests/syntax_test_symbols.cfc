// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component extends="base.Thing" {
//                 @@@@@@@@@@ reference
    public string function alpha() {
//                         @@@@@ definition
        var cb = function() {};
//          @@ definition
        var s = { beta: function() {}, gamma: () => 1 };
//                @@@@ definition
//                                     @@@@@ definition
        doIt({ delta: function() {} });
//      @@@@ reference
        this.epsilon = function() {};
//           @@@@@@@ definition
    }
    function zeta() {}
//           @@@@ definition
}
