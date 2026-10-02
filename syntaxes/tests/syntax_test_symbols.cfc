// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component extends="base.Thing" {
//                 @@@@@@@@@@ reference
    public string function alpha() {
//                         @@@@@ local-definition
//                         @@@@@ global-definition
        var cb = function() {};
//          @@ local-definition
        var s = { beta: function() {}, gamma: () => 1 };
//                @@@@ local-definition
//                                     @@@@@ local-definition
        doIt({ delta: function() {} });
//      @@@@ reference
        this.epsilon = function() {};
//           @@@@@@@ local-definition
    }
    function zeta() {}
//           @@@@ local-definition
//           @@@@ global-definition
}
