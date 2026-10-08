import { ExpressionParsingError } from "./parsing_error.mjs";
import { Scope } from "./scope.mjs";
import { checkSubtype } from "./types.mjs";
import { Literal } from "./definitions/literal.mjs";
import { Assertion } from "./definitions/assertion.mjs";
import { Coercion } from "./definitions/coercion.mjs";
import { EvaluationContext } from "./evaluation_context.mjs";
//#region src/expression/parsing_context.ts
/**
* State associated parsing at a given point in an expression tree.
* @private
*/
var ParsingContext = class ParsingContext {
	constructor(registry, isConstantFunc, path = [], expectedType, scope = new Scope(), errors = []) {
		this.registry = registry;
		this.path = path;
		this.key = path.map((part) => `[${part}]`).join("");
		this.scope = scope;
		this.errors = errors;
		this.expectedType = expectedType;
		this._isConstant = isConstantFunc;
	}
	/**
	* @param expr the JSON expression to parse
	* @param index the optional argument index if this expression is an argument of a parent expression that's being parsed
	* @param options
	* @param options.omitTypeAnnotations set true to omit inferred type annotations.  Caller beware: with this option set, the parsed expression's type will NOT satisfy `expectedType` if it would normally be wrapped in an inferred annotation.
	* @private
	*/
	parse(expr, index, expectedType, bindings, options = {}) {
		if (index != null) return this.concat(index, expectedType, bindings)._parse(expr, options);
		return this._parse(expr, options);
	}
	_parse(expr, options) {
		if (expr === null || typeof expr === "string" || typeof expr === "boolean" || typeof expr === "number") expr = ["literal", expr];
		const key = this.key;
		function annotate(parsed, type, typeAnnotation) {
			if (typeAnnotation === "assert") return new Assertion(type, [parsed], key);
			else if (typeAnnotation === "coerce") return new Coercion(type, [parsed], key);
			else return parsed;
		}
		if (Array.isArray(expr)) {
			if (expr.length === 0) return this.error("Expected an array with at least one element. If you wanted a literal array, use [\"literal\", []].");
			const op = expr[0];
			if (typeof op !== "string") {
				this.error(`Expression name must be a string, but found ${typeof op} instead. If you wanted a literal array, use ["literal", [...]].`, 0);
				return null;
			}
			const Expr = this.registry[op];
			if (Expr) {
				let parsed = Expr.parse(expr, this);
				if (!parsed) return null;
				if (this.expectedType) {
					const expected = this.expectedType;
					const actual = parsed.type;
					if ((expected.kind === "string" || expected.kind === "number" || expected.kind === "boolean" || expected.kind === "object" || expected.kind === "array") && actual.kind === "value") parsed = annotate(parsed, expected, options.typeAnnotation || "assert");
					else if ("projectionDefinition" === expected.kind && [
						"string",
						"array",
						"value"
					].includes(actual.kind) || [
						"color",
						"formatted",
						"resolvedImage"
					].includes(expected.kind) && ["value", "string"].includes(actual.kind) || ["padding", "numberArray"].includes(expected.kind) && [
						"value",
						"number",
						"array"
					].includes(actual.kind) || "colorArray" === expected.kind && [
						"value",
						"string",
						"array"
					].includes(actual.kind) || "variableAnchorOffsetCollection" === expected.kind && ["value", "array"].includes(actual.kind)) parsed = annotate(parsed, expected, options.typeAnnotation || "coerce");
					else if (this.checkSubtype(expected, actual)) return null;
				}
				if (!(parsed instanceof Literal) && parsed.type.kind !== "resolvedImage" && this._isConstant(parsed)) {
					const ec = new EvaluationContext();
					try {
						parsed = new Literal(parsed.type, parsed.evaluate(ec));
					} catch (e) {
						this.error(e.message);
						return null;
					}
				}
				return parsed;
			}
			return this.error(`Unknown expression "${op}". If you wanted a literal array, use ["literal", [...]].`, 0);
		} else if (typeof expr === "undefined") return this.error("'undefined' value invalid. Use null instead.");
		else if (typeof expr === "object") return this.error("Bare objects invalid. Use [\"literal\", {...}] instead.");
		else return this.error(`Expected an array, but found ${typeof expr} instead.`);
	}
	/**
	* Returns a copy of this context suitable for parsing the subexpression at
	* index `index`, optionally appending to 'let' binding map.
	*
	* Note that `errors` property, intended for collecting errors while
	* parsing, is copied by reference rather than cloned.
	* @private
	*/
	concat(index, expectedType, bindings) {
		const path = typeof index === "number" ? this.path.concat(index) : this.path;
		const scope = bindings ? this.scope.concat(bindings) : this.scope;
		return new ParsingContext(this.registry, this._isConstant, path, expectedType || null, scope, this.errors);
	}
	/**
	* Push a parsing (or type checking) error into the `this.errors`
	* @param error The message
	* @param keys Optionally specify the source of the error at a child
	* of the current expression at `this.key`.
	* @private
	*/
	error(error, ...keys) {
		const key = `${this.key}${keys.map((k) => `[${k}]`).join("")}`;
		this.errors.push(new ExpressionParsingError(key, error));
	}
	/**
	* Returns null if `t` is a subtype of `expected`; otherwise returns an
	* error message and also pushes it to `this.errors`.
	* @param expected The expected type
	* @param t The actual type
	* @returns null if `t` is a subtype of `expected`; otherwise returns an error message
	*/
	checkSubtype(expected, t) {
		const error = checkSubtype(expected, t);
		if (error) this.error(error);
		return error;
	}
};
//#endregion
export { ParsingContext };

//# sourceMappingURL=parsing_context.mjs.map