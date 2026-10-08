import { BooleanType, CollatorType, ValueType, typeToString } from "../types.mjs";
import { RuntimeError } from "../runtime_error.mjs";
import { typeOf } from "../values.mjs";
import { Assertion } from "./assertion.mjs";
//#region src/expression/definitions/comparison.ts
function isComparableType(op, type) {
	if (op === "==" || op === "!=") return type.kind === "boolean" || type.kind === "string" || type.kind === "number" || type.kind === "null" || type.kind === "value";
	else return type.kind === "string" || type.kind === "number" || type.kind === "value";
}
function eq(ctx, a, b) {
	return a === b;
}
function neq(ctx, a, b) {
	return a !== b;
}
function lt(ctx, a, b) {
	return a < b;
}
function gt(ctx, a, b) {
	return a > b;
}
function lteq(ctx, a, b) {
	return a <= b;
}
function gteq(ctx, a, b) {
	return a >= b;
}
function eqCollate(ctx, a, b, c) {
	return c.compare(a, b) === 0;
}
function neqCollate(ctx, a, b, c) {
	return !eqCollate(ctx, a, b, c);
}
function ltCollate(ctx, a, b, c) {
	return c.compare(a, b) < 0;
}
function gtCollate(ctx, a, b, c) {
	return c.compare(a, b) > 0;
}
function lteqCollate(ctx, a, b, c) {
	return c.compare(a, b) <= 0;
}
function gteqCollate(ctx, a, b, c) {
	return c.compare(a, b) >= 0;
}
/**
* Special form for comparison operators, implementing the signatures:
* - (T, T, ?Collator) => boolean
* - (T, value, ?Collator) => boolean
* - (value, T, ?Collator) => boolean
*
* For inequalities, T must be either value, string, or number. For ==/!=, it
* can also be boolean or null.
*
* Equality semantics are equivalent to Javascript's strict equality (===/!==)
* -- i.e., when the arguments' types don't match, == evaluates to false, != to
* true.
*
* When types don't match in an ordering comparison, a runtime error is thrown.
*
* @private
*/
function makeComparison(op, compareBasic, compareWithCollator) {
	const isOrderComparison = op !== "==" && op !== "!=";
	return class Comparison {
		constructor(lhs, rhs, key, collator) {
			this.lhs = lhs;
			this.rhs = rhs;
			this.key = key;
			this.collator = collator;
			this.type = BooleanType;
			this.hasUntypedArgument = lhs.type.kind === "value" || rhs.type.kind === "value";
		}
		static parse(args, context) {
			if (args.length !== 3 && args.length !== 4) return context.error("Expected two or three arguments.");
			const op = args[0];
			let lhs = context.parse(args[1], 1, ValueType);
			if (!lhs) return null;
			if (!isComparableType(op, lhs.type)) return context.concat(1).error(`"${op}" comparisons are not supported for type '${typeToString(lhs.type)}'.`);
			let rhs = context.parse(args[2], 2, ValueType);
			if (!rhs) return null;
			if (!isComparableType(op, rhs.type)) return context.concat(2).error(`"${op}" comparisons are not supported for type '${typeToString(rhs.type)}'.`);
			if (lhs.type.kind !== rhs.type.kind && lhs.type.kind !== "value" && rhs.type.kind !== "value") return context.error(`Cannot compare types '${typeToString(lhs.type)}' and '${typeToString(rhs.type)}'.`);
			if (isOrderComparison) {
				if (lhs.type.kind === "value" && rhs.type.kind !== "value") lhs = new Assertion(rhs.type, [lhs], context.key);
				else if (lhs.type.kind !== "value" && rhs.type.kind === "value") rhs = new Assertion(lhs.type, [rhs], context.key);
			}
			let collator = null;
			if (args.length === 4) {
				if (lhs.type.kind !== "string" && rhs.type.kind !== "string" && lhs.type.kind !== "value" && rhs.type.kind !== "value") return context.error("Cannot use collator to compare non-string types.");
				collator = context.parse(args[3], 3, CollatorType);
				if (!collator) return null;
			}
			return new Comparison(lhs, rhs, context.key, collator);
		}
		evaluate(ctx) {
			const lhs = this.lhs.evaluate(ctx);
			const rhs = this.rhs.evaluate(ctx);
			if (isOrderComparison && this.hasUntypedArgument) {
				const lt = typeOf(lhs);
				const rt = typeOf(rhs);
				if (lt.kind !== rt.kind || !(lt.kind === "string" || lt.kind === "number")) throw new RuntimeError(`Expected arguments for "${op}" to be (string, string) or (number, number), but found (${lt.kind}, ${rt.kind}) instead.`, this.key);
			}
			if (this.collator && !isOrderComparison && this.hasUntypedArgument) {
				const lt = typeOf(lhs);
				const rt = typeOf(rhs);
				if (lt.kind !== "string" || rt.kind !== "string") return compareBasic(ctx, lhs, rhs);
			}
			return this.collator ? compareWithCollator(ctx, lhs, rhs, this.collator.evaluate(ctx)) : compareBasic(ctx, lhs, rhs);
		}
		eachChild(fn) {
			fn(this.lhs);
			fn(this.rhs);
			if (this.collator) fn(this.collator);
		}
		outputDefined() {
			return true;
		}
	};
}
const Equals = makeComparison("==", eq, eqCollate);
const NotEquals = makeComparison("!=", neq, neqCollate);
const LessThan = makeComparison("<", lt, ltCollate);
const GreaterThan = makeComparison(">", gt, gtCollate);
const LessThanOrEqual = makeComparison("<=", lteq, lteqCollate);
const GreaterThanOrEqual = makeComparison(">=", gteq, gteqCollate);
//#endregion
export { Equals, GreaterThan, GreaterThanOrEqual, LessThan, LessThanOrEqual, NotEquals };

//# sourceMappingURL=comparison.mjs.map