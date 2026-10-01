// SYNTAX TEST reindent "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
    function f(a) {
        if (a) {
            x = [
                1,
                2
            ];
        } else {
            y = {
                a: 1
            };
        }
        z = doIt(
            a,
            b
        );
        for (var i = 1; i < 2; i++)
            z = i;
        return x;
    }
}
