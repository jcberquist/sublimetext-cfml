// SYNTAX TEST "cfml.tmLanguage"
component {
  var test = {
    key: () => {
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ punctuation.separator.key-value.cfml -entity.name.function.cfml -meta.struct-literal.key.cfml
//      ^ -punctuation.separator.key-value.cfml
//       ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//        ^ punctuation.definition.parameters.end.cfml -punctuation.definition.parameters.begin.cfml
//         ^ -punctuation.definition.parameters.end.cfml -meta.function.parameters.cfml
//          ^ storage.type.function.arrow.cfml
//            ^ -storage.type.function.arrow.cfml
//             ^ meta.function.body.cfml meta.brace.curly.cfml -meta.function.declaration.cfml
//              ^ -meta.brace.curly.cfml
    },
    'key': () => {
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -string.quoted.single.cfml -punctuation.definition.string.end.cfml -meta.struct-literal.key.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//          ^ punctuation.definition.parameters.end.cfml -punctuation.definition.parameters.begin.cfml
//           ^ -punctuation.definition.parameters.end.cfml -meta.function.parameters.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml meta.brace.curly.cfml -meta.function.declaration.cfml
//                ^ -meta.brace.curly.cfml
    },
    "key": () => {
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -punctuation.definition.string.end.cfml -meta.struct-literal.key.cfml -string.quoted.double.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//          ^ punctuation.definition.parameters.end.cfml -punctuation.definition.parameters.begin.cfml
//           ^ -punctuation.definition.parameters.end.cfml -meta.function.parameters.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml meta.brace.curly.cfml -meta.function.declaration.cfml
//                ^ -meta.brace.curly.cfml
    },
    key: () => test,
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -entity.name.function.cfml
//      ^ -punctuation.separator.key-value.cfml
//       ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//        ^ punctuation.definition.parameters.end.cfml -punctuation.definition.parameters.begin.cfml
//         ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//          ^ storage.type.function.arrow.cfml
//            ^ -storage.type.function.arrow.cfml
//             ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                 ^ -meta.function.body.cfml -variable.other.readwrite.cfml
    'key': () => test,
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -punctuation.definition.string.end.cfml -meta.struct-literal.key.cfml -string.quoted.single.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//          ^ punctuation.definition.parameters.end.cfml -punctuation.definition.parameters.begin.cfml
//           ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                   ^ -meta.function.body.cfml -variable.other.readwrite.cfml
    "key": () => test
//  ^ meta.function.declaration.cfml meta.struct-literal.key.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -punctuation.definition.string.end.cfml -meta.struct-literal.key.cfml -string.quoted.double.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//          ^ punctuation.definition.parameters.end.cfml -punctuation.definition.parameters.begin.cfml
//           ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                   ^ -variable.other.readwrite.cfml
  }

  (i) => { return i * 2 }
  // <- meta.function.anonymous.cfml meta.function.declaration.cfml meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
// ^ variable.parameter.function.cfml -punctuation.definition.parameters.begin.cfml
//  ^ punctuation.definition.parameters.end.cfml -variable.parameter.function.cfml
//   ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//    ^ storage.type.function.arrow.cfml
//      ^ -storage.type.function.arrow.cfml
//       ^ meta.function.body.cfml meta.brace.curly.cfml -meta.function.declaration.cfml -meta.function.anonymous.cfml
//        ^ -meta.brace.curly.cfml
//         ^ keyword.control.flow.cfml
//               ^ -keyword.control.flow.cfml
//                ^ variable.other.readwrite.cfml
//                 ^ -variable.other.readwrite.cfml
//                  ^ keyword.operator.arithmetic.cfml
//                   ^ -keyword.operator.arithmetic.cfml
//                    ^ constant.numeric.cfml
//                     ^ -constant.numeric.cfml
//                      ^ meta.brace.curly.cfml
//                       ^ -meta.brace.curly.cfml -meta.function.body.cfml

  a.b = (i) => i * 2;
  // <- meta.function.declaration.cfml support.class.cfml
// ^ punctuation.accessor.cfml -support.class.cfml
//  ^ meta.property.cfml entity.name.function.cfml -punctuation.accessor.cfml
//   ^ -meta.property.cfml -entity.name.function.cfml
//    ^ keyword.operator.assignment.cfml
//     ^ -keyword.operator.assignment.cfml
//      ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//       ^ variable.parameter.function.cfml -punctuation.definition.parameters.begin.cfml
//        ^ punctuation.definition.parameters.end.cfml -variable.parameter.function.cfml
//         ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//          ^ storage.type.function.arrow.cfml
//            ^ -storage.type.function.arrow.cfml
//             ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//              ^ -variable.other.readwrite.cfml
//               ^ keyword.operator.arithmetic.cfml
//                ^ -keyword.operator.arithmetic.cfml
//                 ^ constant.numeric.cfml
//                  ^ punctuation.terminator.statement.cfml -constant.numeric.cfml -meta.function.body.cfml
//                   ^ -punctuation.terminator.statement.cfml

  var test = ( param ) => param * 2;
  // <- storage.type.cfml
//   ^ -storage.type.cfml
//    ^ meta.function.declaration.cfml variable.other.readwrite.cfml entity.name.function.cfml
//        ^ -entity.name.function.cfml -variable.other.readwrite.cfml
//         ^ keyword.operator.assignment.cfml
//          ^ -keyword.operator.assignment.cfml
//           ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//            ^ -punctuation.definition.parameters.begin.cfml
//             ^ variable.parameter.function.cfml
//                  ^ -variable.parameter.function.cfml
//                   ^ punctuation.definition.parameters.end.cfml
//                    ^ -punctuation.definition.parameters.end.cfml -meta.function.parameters.cfml
//                     ^ storage.type.function.arrow.cfml
//                       ^ -storage.type.function.arrow.cfml
//                        ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                             ^ -variable.other.readwrite.cfml
//                              ^ keyword.operator.arithmetic.cfml
//                               ^ -keyword.operator.arithmetic.cfml
//                                ^ constant.numeric.cfml
//                                 ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -constant.numeric.cfml
//                                  ^ -punctuation.terminator.statement.cfml
  var test = ( param ) => { param * 2 };
  // <- storage.type.cfml
//   ^ -storage.type.cfml
//    ^ meta.function.declaration.cfml variable.other.readwrite.cfml entity.name.function.cfml
//        ^ -variable.other.readwrite.cfml -entity.name.function.cfml
//         ^ keyword.operator.assignment.cfml
//          ^ -keyword.operator.assignment.cfml
//           ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//            ^ -punctuation.definition.parameters.begin.cfml
//             ^ variable.parameter.function.cfml
//                  ^ -variable.parameter.function.cfml
//                   ^ punctuation.definition.parameters.end.cfml
//                    ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//                     ^ storage.type.function.arrow.cfml
//                       ^ -storage.type.function.arrow.cfml
//                        ^ meta.function.body.cfml meta.brace.curly.cfml -meta.function.declaration.cfml
//                         ^ -meta.brace.curly.cfml
//                          ^ variable.other.readwrite.cfml
//                               ^ -variable.other.readwrite.cfml
//                                ^ keyword.operator.arithmetic.cfml
//                                 ^ -keyword.operator.arithmetic.cfml
//                                  ^ constant.numeric.cfml
//                                   ^ -constant.numeric.cfml
//                                    ^ meta.brace.curly.cfml
//                                     ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -meta.brace.curly.cfml
//                                      ^ -punctuation.terminator.statement.cfml

  var a
  .b = (t) => { t + 3 };
  // <- punctuation.accessor.cfml
// ^ meta.function.declaration.cfml meta.property.cfml entity.name.function.cfml -punctuation.accessor.cfml
//  ^ -meta.property.cfml -entity.name.function.cfml
//   ^ keyword.operator.assignment.cfml
//    ^ -keyword.operator.assignment.cfml
//     ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//      ^ variable.parameter.function.cfml -punctuation.definition.parameters.begin.cfml
//       ^ punctuation.definition.parameters.end.cfml -variable.parameter.function.cfml
//        ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//         ^ storage.type.function.arrow.cfml
//           ^ -storage.type.function.arrow.cfml
//            ^ meta.function.body.cfml meta.brace.curly.cfml -meta.function.declaration.cfml
//             ^ -meta.brace.curly.cfml
//              ^ variable.other.readwrite.cfml
//               ^ -variable.other.readwrite.cfml
//                ^ keyword.operator.arithmetic.cfml
//                 ^ -keyword.operator.arithmetic.cfml
//                  ^ constant.numeric.cfml
//                   ^ -constant.numeric.cfml
//                    ^ meta.brace.curly.cfml
//                     ^ punctuation.terminator.statement.cfml -meta.brace.curly.cfml -meta.function.body.cfml
//                      ^ -punctuation.terminator.statement.cfml

  var a
  .b = (t) => t + 3;
  // <- punctuation.accessor.cfml
// ^ meta.function.declaration.cfml meta.property.cfml entity.name.function.cfml -punctuation.accessor.cfml
//  ^ -meta.property.cfml -entity.name.function.cfml
//   ^ keyword.operator.assignment.cfml
//    ^ -keyword.operator.assignment.cfml
//     ^ meta.function.parameters.cfml punctuation.definition.parameters.begin.cfml
//      ^ variable.parameter.function.cfml -punctuation.definition.parameters.begin.cfml
//       ^ punctuation.definition.parameters.end.cfml -variable.parameter.function.cfml
//        ^ -meta.function.parameters.cfml -punctuation.definition.parameters.end.cfml
//         ^ storage.type.function.arrow.cfml
//           ^ -storage.type.function.arrow.cfml
//            ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//             ^ -variable.other.readwrite.cfml
//              ^ keyword.operator.arithmetic.cfml
//               ^ -keyword.operator.arithmetic.cfml
//                ^ constant.numeric.cfml
//                 ^ punctuation.terminator.statement.cfml -constant.numeric.cfml -meta.function.body.cfml
//                  ^ -punctuation.terminator.statement.cfml

}