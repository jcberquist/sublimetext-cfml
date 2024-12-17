// SYNTAX TEST "Packages/CFML/syntaxes/CFML.sublime-syntax"
component {
  var test = {
    key: () => {
//  ^ meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -entity.name.function.cfml
//      ^ -punctuation.separator.key-value.cfml
//       ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//        ^ punctuation.section.parameters.end.cfml -punctuation.section.parameters.begin.cfml
//         ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//          ^ storage.type.function.arrow.cfml
//            ^ -storage.type.function.arrow.cfml
//             ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//              ^ -punctuation.section.block.begin.cfml
    },
    'key': () => {
//  ^ meta.struct-literal.key.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -string.quoted.single.cfml -punctuation.definition.string.end.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//          ^ punctuation.section.parameters.end.cfml -punctuation.section.parameters.begin.cfml
//           ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//                ^ -punctuation.section.block.begin.cfml
    },
    "key": () => {
//  ^ meta.struct-literal.key.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -punctuation.definition.string.end.cfml -string.quoted.double.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//          ^ punctuation.section.parameters.end.cfml -punctuation.section.parameters.begin.cfml
//           ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//                ^ -punctuation.section.block.begin.cfml
    },
    key: () => test,
//  ^ meta.struct-literal.key.cfml entity.name.function.cfml
//     ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -entity.name.function.cfml
//      ^ -punctuation.separator.key-value.cfml
//       ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//        ^ punctuation.section.parameters.end.cfml -punctuation.section.parameters.begin.cfml
//         ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//          ^ storage.type.function.arrow.cfml
//            ^ -storage.type.function.arrow.cfml
//             ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                 ^ -meta.function.body.cfml -variable.other.readwrite.cfml
    'key': () => test,
//  ^ meta.struct-literal.key.cfml string.quoted.single.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -string.quoted.single.cfml -punctuation.definition.string.end.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//          ^ punctuation.section.parameters.end.cfml -punctuation.section.parameters.begin.cfml
//           ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                   ^ -meta.function.body.cfml -variable.other.readwrite.cfml
    "key": () => test
//  ^ meta.struct-literal.key.cfml string.quoted.double.cfml punctuation.definition.string.begin.cfml
//   ^ entity.name.function.cfml -punctuation.definition.string.begin.cfml
//      ^ punctuation.definition.string.end.cfml -entity.name.function.cfml
//       ^ punctuation.separator.key-value.cfml -meta.struct-literal.key.cfml -punctuation.definition.string.end.cfml -string.quoted.double.cfml
//        ^ -punctuation.separator.key-value.cfml
//         ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//          ^ punctuation.section.parameters.end.cfml -punctuation.section.parameters.begin.cfml
//           ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//            ^ storage.type.function.arrow.cfml
//              ^ -storage.type.function.arrow.cfml
//               ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                   ^ -variable.other.readwrite.cfml
  }

  test((i) => { return i * 2 })
//     ^ meta.function.declaration.cfml meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//      ^ variable.parameter.function.cfml -punctuation.section.parameters.begin.cfml
//       ^ punctuation.section.parameters.end.cfml -variable.parameter.function.cfml
//        ^ -punctuation.section.parameters.end.cfml -meta.function.parameters.cfml
//         ^ storage.type.function.arrow.cfml
//           ^ -storage.type.function.arrow.cfml
//            ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//             ^ -punctuation.section.block.begin.cfml
//              ^ keyword.control.flow.return.cfml
//                    ^ -keyword.control.flow.cfml
//                     ^ variable.other.readwrite.cfml
//                      ^ -variable.other.readwrite.cfml
//                       ^ keyword.operator.arithmetic.binary.cfml
//                        ^ -keyword.operator.arithmetic.binary.cfml
//                         ^ constant.numeric.cfml
//                          ^ -constant.numeric.cfml
//                           ^ punctuation.section.block.end.cfml
//                            ^  -meta.function.anonymous.cfml -meta.function.body.cfml -punctuation.section.block.end.cfml

  a.b = (i) => i * 2;
// ^ punctuation.accessor.cfml -support.class.cfml
//  ^ entity.name.function.cfml -punctuation.accessor.cfml
//   ^ -meta.property.cfml -entity.name.function.cfml
//    ^ keyword.operator.assignment.cfml
//     ^ -keyword.operator.assignment.cfml
//      ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//       ^ variable.parameter.function.cfml -punctuation.section.parameters.begin.cfml
//        ^ punctuation.section.parameters.end.cfml -variable.parameter.function.cfml
//         ^ -meta.function.parameters.cfml -punctuation.section.parameters.end.cfml
//          ^ storage.type.function.arrow.cfml
//            ^ -storage.type.function.arrow.cfml
//             ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//              ^ -variable.other.readwrite.cfml
//               ^ keyword.operator.arithmetic.binary.cfml
//                ^ -keyword.operator.arithmetic.binary.cfml
//                 ^ constant.numeric.cfml
//                  ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -constant.numeric.cfml
//                   ^ -punctuation.terminator.statement.cfml

  var test = ( param ) => param * 2;
  // <- keyword.declaration.cfml
//   ^ -keyword.declaration.cfml
//    ^ entity.name.function.cfml variable.other.readwrite.cfml 
//        ^ -variable.other.readwrite.cfml -entity.name.function.cfml
//         ^ keyword.operator.assignment.cfml
//          ^ -keyword.operator.assignment.cfml
//           ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//            ^ -punctuation.section.parameters.begin.cfml
//             ^ variable.parameter.function.cfml
//                  ^ -variable.parameter.function.cfml
//                   ^ punctuation.section.parameters.end.cfml
//                    ^ -meta.function.parameters.cfml -punctuation.section.parameters.end.cfml
//                     ^ storage.type.function.arrow.cfml
//                       ^ -storage.type.function.arrow.cfml
//                        ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                             ^ -variable.other.readwrite.cfml
//                              ^ keyword.operator.arithmetic.binary.cfml
//                               ^ -keyword.operator.arithmetic.binary.cfml
//                                ^ constant.numeric.cfml
//                                 ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -constant.numeric.cfml
//                                  ^ -punctuation.terminator.statement.cfml

  var test = ( param ) => { param * 2 };
  // <- keyword.declaration.cfml
//   ^ -keyword.declaration.cfml
//    ^ entity.name.function.cfml variable.other.readwrite.cfml 
//        ^ -variable.other.readwrite.cfml -entity.name.function.cfml
//         ^ keyword.operator.assignment.cfml
//          ^ -keyword.operator.assignment.cfml
//           ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//            ^ -punctuation.section.parameters.begin.cfml
//             ^ variable.parameter.function.cfml
//                  ^ -variable.parameter.function.cfml
//                   ^ punctuation.section.parameters.end.cfml
//                    ^ -meta.function.parameters.cfml -punctuation.section.parameters.end.cfml
//                     ^ storage.type.function.arrow.cfml
//                       ^ -storage.type.function.arrow.cfml
//                        ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//                         ^ -punctuation.section.block.begin.cfml
//                          ^ variable.other.readwrite.cfml
//                               ^ -variable.other.readwrite.cfml
//                                ^ keyword.operator.arithmetic.binary.cfml
//                                 ^ -keyword.operator.arithmetic.binary.cfml
//                                  ^ constant.numeric.cfml
//                                   ^ -constant.numeric.cfml
//                                    ^ punctuation.section.block.end.cfml
//                                     ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -punctuation.section.block.end.cfml
//                                      ^ -punctuation.terminator.statement.cfml

  var a
  .b = (t) => { t + 3 };
  // <- punctuation.accessor.cfml
// ^ entity.name.function.cfml variable.other.readwrite.cfml -punctuation.accessor.cfml
//  ^ -entity.name.function.cfml -variable.other.readwrite.cfml
//   ^ keyword.operator.assignment.cfml
//    ^ -keyword.operator.assignment.cfml
//     ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//      ^ variable.parameter.function.cfml -punctuation.section.parameters.begin.cfml
//       ^ punctuation.section.parameters.end.cfml -variable.parameter.function.cfml
//        ^ -meta.function.parameters.cfml -punctuation.section.parameters.end.cfml
//         ^ storage.type.function.arrow.cfml
//           ^ -storage.type.function.arrow.cfml
//            ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//             ^ -punctuation.section.block.begin.cfml
//              ^ variable.other.readwrite.cfml
//               ^ -variable.other.readwrite.cfml
//                ^ keyword.operator.arithmetic.binary.cfml
//                 ^ -keyword.operator.arithmetic.binary.cfml
//                  ^ constant.numeric.cfml
//                   ^ -constant.numeric.cfml
//                    ^ punctuation.section.block.end.cfml
//                     ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -punctuation.section.block.end.cfml
//                      ^ -punctuation.terminator.statement.cfml

  var a
  .b = (t) => t + 3;
  // <- punctuation.accessor.cfml
// ^ entity.name.function.cfml variable.other.readwrite.cfml -punctuation.accessor.cfml
//  ^ -meta.property.cfml -entity.name.function.cfml
//   ^ keyword.operator.assignment.cfml
//    ^ -keyword.operator.assignment.cfml
//     ^ meta.function.parameters.cfml punctuation.section.parameters.begin.cfml
//      ^ variable.parameter.function.cfml -punctuation.section.parameters.begin.cfml
//       ^ punctuation.section.parameters.end.cfml -variable.parameter.function.cfml
//        ^ -meta.function.parameters.cfml -punctuation.section.parameters.end.cfml
//         ^ storage.type.function.arrow.cfml
//           ^ -storage.type.function.arrow.cfml
//            ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//             ^ -variable.other.readwrite.cfml
//              ^ keyword.operator.arithmetic.binary.cfml
//               ^ -keyword.operator.arithmetic.binary.cfml
//                ^ constant.numeric.cfml
//                 ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -constant.numeric.cfml
//                  ^ -punctuation.terminator.statement.cfml

var test = (a) =>
{ }
// <- source.cfml.script meta.class.body.cfml meta.function.body.cfml punctuation.section.block.begin.cfml -meta.struct-literal.cfml

  var test = param => param * 2;
  // <- keyword.declaration.cfml
//   ^ -keyword.declaration.cfml
//    ^ entity.name.function.cfml variable.other.readwrite.cfml
//        ^ -variable.other.readwrite.cfml -entity.name.function.cfml
//         ^ keyword.operator.assignment.cfml
//          ^ -keyword.operator.assignment.cfml
//           ^ variable.parameter.function.cfml
//                ^ -variable.parameter.function.cfml
//                 ^ storage.type.function.arrow.cfml
//                   ^ -storage.type.function.arrow.cfml
//                    ^ meta.function.body.cfml variable.other.readwrite.cfml -meta.function.declaration.cfml
//                         ^ -variable.other.readwrite.cfml
//                          ^ keyword.operator.arithmetic.binary.cfml
//                           ^ -keyword.operator.arithmetic.binary.cfml
//                            ^ constant.numeric.cfml
//                             ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -constant.numeric.cfml
//                              ^ -punctuation.terminator.statement.cfml

  var test = param => { param * 2 };
  // <- keyword.declaration.cfml
//   ^ -keyword.declaration.cfml
//    ^ entity.name.function.cfml variable.other.readwrite.cfml 
//        ^ -variable.other.readwrite.cfml -entity.name.function.cfml
//         ^ keyword.operator.assignment.cfml
//          ^ -keyword.operator.assignment.cfml//
//           ^ variable.parameter.function.cfml
//                ^ -variable.parameter.function.cfml
//                 ^ storage.type.function.arrow.cfml
//                   ^ -storage.type.function.arrow.cfml
//                    ^ meta.function.body.cfml punctuation.section.block.begin.cfml -meta.function.declaration.cfml
//                     ^ -punctuation.section.block.begin.cfml
//                      ^ variable.other.readwrite.cfml
//                           ^ -variable.other.readwrite.cfml
//                            ^ keyword.operator.arithmetic.binary.cfml
//                             ^ -keyword.operator.arithmetic.binary.cfml
//                              ^ constant.numeric.cfml
//                               ^ -constant.numeric.cfml
//                                ^ punctuation.section.block.end.cfml
//                                 ^ punctuation.terminator.statement.cfml -meta.function.body.cfml -punctuation.section.block.end.cfml
//                                  ^ -punctuation.terminator.statement.cfml

  test((a) => 1);
  //    ^ variable.parameter.function.cfml
  //       ^^ storage.type.function.arrow.cfml

  test(a => 1);
  //   ^ variable.parameter.function.cfml
  //     ^^ storage.type.function.arrow.cfml
}
