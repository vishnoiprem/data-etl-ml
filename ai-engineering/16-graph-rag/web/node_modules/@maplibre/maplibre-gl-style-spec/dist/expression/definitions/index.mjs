import { Literal } from "./literal.mjs";
import { Assertion } from "./assertion.mjs";
import { Coercion } from "./coercion.mjs";
import { Let } from "./let.mjs";
import { Var } from "./var.mjs";
import { At } from "./at.mjs";
import { In } from "./in.mjs";
import { IndexOf } from "./index_of.mjs";
import { Match } from "./match.mjs";
import { Case } from "./case.mjs";
import { Slice } from "./slice.mjs";
import { Step } from "./step.mjs";
import { Interpolate } from "./interpolate.mjs";
import { Coalesce } from "./coalesce.mjs";
import { Equals, GreaterThan, GreaterThanOrEqual, LessThan, LessThanOrEqual, NotEquals } from "./comparison.mjs";
import { CollatorExpression } from "./collator.mjs";
import { NumberFormat } from "./number_format.mjs";
import { FormatExpression } from "./format.mjs";
import { ImageExpression } from "./image.mjs";
import { Length } from "./length.mjs";
import { Within } from "./within.mjs";
import { Distance } from "./distance.mjs";
import { Semiliteral } from "./semiliteral.mjs";
import { GlobalState } from "./global_state.mjs";
//#region src/expression/definitions/index.ts
const expressions = {
	"==": Equals,
	"!=": NotEquals,
	">": GreaterThan,
	"<": LessThan,
	">=": GreaterThanOrEqual,
	"<=": LessThanOrEqual,
	array: Assertion,
	at: At,
	boolean: Assertion,
	case: Case,
	coalesce: Coalesce,
	collator: CollatorExpression,
	format: FormatExpression,
	image: ImageExpression,
	in: In,
	"index-of": IndexOf,
	interpolate: Interpolate,
	"interpolate-hcl": Interpolate,
	"interpolate-lab": Interpolate,
	length: Length,
	let: Let,
	literal: Literal,
	match: Match,
	number: Assertion,
	"number-format": NumberFormat,
	object: Assertion,
	semiliteral: Semiliteral,
	slice: Slice,
	step: Step,
	string: Assertion,
	"to-boolean": Coercion,
	"to-color": Coercion,
	"to-number": Coercion,
	"to-string": Coercion,
	var: Var,
	within: Within,
	distance: Distance,
	"global-state": GlobalState
};
//#endregion
export { expressions };

//# sourceMappingURL=index.mjs.map