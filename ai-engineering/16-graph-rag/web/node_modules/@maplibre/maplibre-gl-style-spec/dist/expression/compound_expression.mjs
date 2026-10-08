import { BooleanType, CollatorType, ColorType, ErrorType, NumberType, ObjectType, StringType, ValueType, array, typeToString } from "./types.mjs";
import { Color } from "./types/color.mjs";
import { RuntimeError } from "./runtime_error.mjs";
import { typeOf, validateRGBA, valueToString } from "./values.mjs";
import { Literal } from "./definitions/literal.mjs";
import { Assertion } from "./definitions/assertion.mjs";
import { Coercion } from "./definitions/coercion.mjs";
import { ParsingContext } from "./parsing_context.mjs";
import { Var } from "./definitions/var.mjs";
import { CollatorExpression } from "./definitions/collator.mjs";
import { Within } from "./definitions/within.mjs";
import { Distance } from "./definitions/distance.mjs";
import { GlobalState } from "./definitions/global_state.mjs";
import { expressions } from "./definitions/index.mjs";
//#region src/expression/compound_expression.ts
var CompoundExpression = class CompoundExpression {
	constructor(name, type, evaluate, args, key) {
		this.name = name;
		this.type = type;
		this._evaluate = evaluate;
		this.args = args;
		this.key = key;
	}
	evaluate(ctx) {
		return this._evaluate(ctx, this.args, this.key);
	}
	eachChild(fn) {
		this.args.forEach(fn);
	}
	outputDefined() {
		return false;
	}
	static parse(args, context) {
		const op = args[0];
		const definition = CompoundExpression.definitions[op];
		if (!definition) return context.error(`Unknown expression "${op}". If you wanted a literal array, use ["literal", [...]].`, 0);
		const type = Array.isArray(definition) ? definition[0] : definition.type;
		const availableOverloads = Array.isArray(definition) ? [[definition[1], definition[2]]] : definition.overloads;
		const overloads = availableOverloads.filter(([signature]) => !Array.isArray(signature) || signature.length === args.length - 1);
		let signatureContext = null;
		for (const [params, evaluate] of overloads) {
			signatureContext = new ParsingContext(context.registry, isExpressionConstant, context.path, null, context.scope);
			const parsedArgs = [];
			let argParseFailed = false;
			for (let i = 1; i < args.length; i++) {
				const arg = args[i];
				const expectedType = Array.isArray(params) ? params[i - 1] : params.type;
				const parsed = signatureContext.parse(arg, 1 + parsedArgs.length, expectedType);
				if (!parsed) {
					argParseFailed = true;
					break;
				}
				parsedArgs.push(parsed);
			}
			if (argParseFailed) continue;
			if (Array.isArray(params)) {
				if (params.length !== parsedArgs.length) {
					signatureContext.error(`Expected ${params.length} arguments, but found ${parsedArgs.length} instead.`);
					continue;
				}
			}
			for (let i = 0; i < parsedArgs.length; i++) {
				const expected = Array.isArray(params) ? params[i] : params.type;
				const arg = parsedArgs[i];
				signatureContext.concat(i + 1).checkSubtype(expected, arg.type);
			}
			if (signatureContext.errors.length === 0) return new CompoundExpression(op, type, evaluate, parsedArgs, context.key);
		}
		if (overloads.length === 1) context.errors.push(...signatureContext.errors);
		else {
			const signatures = (overloads.length ? overloads : availableOverloads).map(([params]) => stringifySignature(params)).join(" | ");
			const actualTypes = [];
			for (let i = 1; i < args.length; i++) {
				const parsed = context.parse(args[i], 1 + actualTypes.length);
				if (!parsed) return null;
				actualTypes.push(typeToString(parsed.type));
			}
			context.error(`Expected arguments of type ${signatures}, but found (${actualTypes.join(", ")}) instead.`);
		}
		return null;
	}
	static register(registry, definitions) {
		CompoundExpression.definitions = definitions;
		for (const name in definitions) registry[name] = CompoundExpression;
	}
};
function rgba(ctx, [r, g, b, a], key) {
	r = r.evaluate(ctx);
	g = g.evaluate(ctx);
	b = b.evaluate(ctx);
	const alpha = a ? a.evaluate(ctx) : 1;
	const error = validateRGBA(r, g, b, alpha);
	if (error) throw new RuntimeError(error, key);
	return new Color(r / 255, g / 255, b / 255, alpha, false);
}
function has(key, obj) {
	return key in obj && obj[key] !== void 0;
}
function get(key, obj) {
	const v = obj[key];
	return typeof v === "undefined" ? null : v;
}
function binarySearch(v, a, i, j) {
	while (i <= j) {
		const m = i + j >> 1;
		if (a[m] === v) return true;
		if (a[m] > v) j = m - 1;
		else i = m + 1;
	}
	return false;
}
function varargs(type) {
	return { type };
}
CompoundExpression.register(expressions, {
	error: [
		ErrorType,
		[StringType],
		(ctx, [v], key) => {
			throw new RuntimeError(v.evaluate(ctx), key);
		}
	],
	typeof: [
		StringType,
		[ValueType],
		(ctx, [v]) => typeToString(typeOf(v.evaluate(ctx)))
	],
	"to-rgba": [
		array(NumberType, 4),
		[ColorType],
		(ctx, [v]) => {
			const [r, g, b, a] = v.evaluate(ctx).rgb;
			return [
				r * 255,
				g * 255,
				b * 255,
				a
			];
		}
	],
	rgb: [
		ColorType,
		[
			NumberType,
			NumberType,
			NumberType
		],
		rgba
	],
	rgba: [
		ColorType,
		[
			NumberType,
			NumberType,
			NumberType,
			NumberType
		],
		rgba
	],
	has: {
		type: BooleanType,
		overloads: [[[StringType], (ctx, [key]) => has(key.evaluate(ctx), ctx.properties())], [[StringType, ObjectType], (ctx, [key, obj]) => has(key.evaluate(ctx), obj.evaluate(ctx))]]
	},
	get: {
		type: ValueType,
		overloads: [[[StringType], (ctx, [key]) => get(key.evaluate(ctx), ctx.properties())], [[StringType, ObjectType], (ctx, [key, obj]) => get(key.evaluate(ctx), obj.evaluate(ctx))]]
	},
	"feature-state": [
		ValueType,
		[StringType],
		(ctx, [key]) => get(key.evaluate(ctx), ctx.featureState || {})
	],
	properties: [
		ObjectType,
		[],
		(ctx) => ctx.properties()
	],
	"geometry-type": [
		StringType,
		[],
		(ctx) => ctx.geometryType()
	],
	id: [
		ValueType,
		[],
		(ctx) => ctx.id()
	],
	zoom: [
		NumberType,
		[],
		(ctx) => ctx.globals.zoom
	],
	"heatmap-density": [
		NumberType,
		[],
		(ctx) => ctx.globals.heatmapDensity || 0
	],
	elevation: [
		NumberType,
		[],
		(ctx) => ctx.globals.elevation || 0
	],
	"line-progress": [
		NumberType,
		[],
		(ctx) => ctx.globals.lineProgress || 0
	],
	accumulated: [
		ValueType,
		[],
		(ctx) => ctx.globals.accumulated === void 0 ? null : ctx.globals.accumulated
	],
	"+": [
		NumberType,
		varargs(NumberType),
		(ctx, args) => {
			let result = 0;
			for (const arg of args) result += arg.evaluate(ctx);
			return result;
		}
	],
	"*": [
		NumberType,
		varargs(NumberType),
		(ctx, args) => {
			let result = 1;
			for (const arg of args) result *= arg.evaluate(ctx);
			return result;
		}
	],
	"-": {
		type: NumberType,
		overloads: [[[NumberType, NumberType], (ctx, [a, b]) => a.evaluate(ctx) - b.evaluate(ctx)], [[NumberType], (ctx, [a]) => -a.evaluate(ctx)]]
	},
	"/": [
		NumberType,
		[NumberType, NumberType],
		(ctx, [a, b]) => a.evaluate(ctx) / b.evaluate(ctx)
	],
	"%": [
		NumberType,
		[NumberType, NumberType],
		(ctx, [a, b]) => a.evaluate(ctx) % b.evaluate(ctx)
	],
	ln2: [
		NumberType,
		[],
		() => Math.LN2
	],
	pi: [
		NumberType,
		[],
		() => Math.PI
	],
	e: [
		NumberType,
		[],
		() => Math.E
	],
	"^": [
		NumberType,
		[NumberType, NumberType],
		(ctx, [b, e]) => Math.pow(b.evaluate(ctx), e.evaluate(ctx))
	],
	sqrt: [
		NumberType,
		[NumberType],
		(ctx, [x]) => Math.sqrt(x.evaluate(ctx))
	],
	log10: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.log(n.evaluate(ctx)) / Math.LN10
	],
	ln: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.log(n.evaluate(ctx))
	],
	log2: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.log(n.evaluate(ctx)) / Math.LN2
	],
	sin: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.sin(n.evaluate(ctx))
	],
	cos: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.cos(n.evaluate(ctx))
	],
	tan: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.tan(n.evaluate(ctx))
	],
	asin: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.asin(n.evaluate(ctx))
	],
	acos: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.acos(n.evaluate(ctx))
	],
	atan: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.atan(n.evaluate(ctx))
	],
	min: [
		NumberType,
		varargs(NumberType),
		(ctx, args) => Math.min(...args.map((arg) => arg.evaluate(ctx)))
	],
	max: [
		NumberType,
		varargs(NumberType),
		(ctx, args) => Math.max(...args.map((arg) => arg.evaluate(ctx)))
	],
	abs: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.abs(n.evaluate(ctx))
	],
	round: [
		NumberType,
		[NumberType],
		(ctx, [n]) => {
			const v = n.evaluate(ctx);
			return v < 0 ? -Math.round(-v) : Math.round(v);
		}
	],
	floor: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.floor(n.evaluate(ctx))
	],
	ceil: [
		NumberType,
		[NumberType],
		(ctx, [n]) => Math.ceil(n.evaluate(ctx))
	],
	"filter-==": [
		BooleanType,
		[StringType, ValueType],
		(ctx, [k, v]) => ctx.properties()[k.value] === v.value
	],
	"filter-id-==": [
		BooleanType,
		[ValueType],
		(ctx, [v]) => ctx.id() === v.value
	],
	"filter-type-==": [
		BooleanType,
		[StringType],
		(ctx, [v]) => ctx.geometryType() === v.value
	],
	"filter-<": [
		BooleanType,
		[StringType, ValueType],
		(ctx, [k, v]) => {
			const a = ctx.properties()[k.value];
			const b = v.value;
			return typeof a === typeof b && a < b;
		}
	],
	"filter-id-<": [
		BooleanType,
		[ValueType],
		(ctx, [v]) => {
			const a = ctx.id();
			const b = v.value;
			return typeof a === typeof b && a < b;
		}
	],
	"filter->": [
		BooleanType,
		[StringType, ValueType],
		(ctx, [k, v]) => {
			const a = ctx.properties()[k.value];
			const b = v.value;
			return typeof a === typeof b && a > b;
		}
	],
	"filter-id->": [
		BooleanType,
		[ValueType],
		(ctx, [v]) => {
			const a = ctx.id();
			const b = v.value;
			return typeof a === typeof b && a > b;
		}
	],
	"filter-<=": [
		BooleanType,
		[StringType, ValueType],
		(ctx, [k, v]) => {
			const a = ctx.properties()[k.value];
			const b = v.value;
			return typeof a === typeof b && a <= b;
		}
	],
	"filter-id-<=": [
		BooleanType,
		[ValueType],
		(ctx, [v]) => {
			const a = ctx.id();
			const b = v.value;
			return typeof a === typeof b && a <= b;
		}
	],
	"filter->=": [
		BooleanType,
		[StringType, ValueType],
		(ctx, [k, v]) => {
			const a = ctx.properties()[k.value];
			const b = v.value;
			return typeof a === typeof b && a >= b;
		}
	],
	"filter-id->=": [
		BooleanType,
		[ValueType],
		(ctx, [v]) => {
			const a = ctx.id();
			const b = v.value;
			return typeof a === typeof b && a >= b;
		}
	],
	"filter-has": [
		BooleanType,
		[ValueType],
		(ctx, [k]) => {
			const key = k.value;
			const props = ctx.properties();
			return key in props && props[key] !== void 0;
		}
	],
	"filter-has-id": [
		BooleanType,
		[],
		(ctx) => ctx.id() !== null && ctx.id() !== void 0
	],
	"filter-type-in": [
		BooleanType,
		[array(StringType)],
		(ctx, [v]) => v.value.indexOf(ctx.geometryType()) >= 0
	],
	"filter-id-in": [
		BooleanType,
		[array(ValueType)],
		(ctx, [v]) => v.value.indexOf(ctx.id()) >= 0
	],
	"filter-in-small": [
		BooleanType,
		[StringType, array(ValueType)],
		(ctx, [k, v]) => v.value.indexOf(ctx.properties()[k.value]) >= 0
	],
	"filter-in-large": [
		BooleanType,
		[StringType, array(ValueType)],
		(ctx, [k, v]) => binarySearch(ctx.properties()[k.value], v.value, 0, v.value.length - 1)
	],
	all: {
		type: BooleanType,
		overloads: [[[BooleanType, BooleanType], (ctx, [a, b]) => a.evaluate(ctx) && b.evaluate(ctx)], [varargs(BooleanType), (ctx, args) => {
			for (const arg of args) if (!arg.evaluate(ctx)) return false;
			return true;
		}]]
	},
	any: {
		type: BooleanType,
		overloads: [[[BooleanType, BooleanType], (ctx, [a, b]) => a.evaluate(ctx) || b.evaluate(ctx)], [varargs(BooleanType), (ctx, args) => {
			for (const arg of args) if (arg.evaluate(ctx)) return true;
			return false;
		}]]
	},
	"!": [
		BooleanType,
		[BooleanType],
		(ctx, [b]) => !b.evaluate(ctx)
	],
	"is-supported-script": [
		BooleanType,
		[StringType],
		(ctx, [s]) => {
			const isSupportedScript = ctx.globals && ctx.globals.isSupportedScript;
			if (isSupportedScript) return isSupportedScript(s.evaluate(ctx));
			return true;
		}
	],
	upcase: [
		StringType,
		[StringType],
		(ctx, [s]) => s.evaluate(ctx).toUpperCase()
	],
	downcase: [
		StringType,
		[StringType],
		(ctx, [s]) => s.evaluate(ctx).toLowerCase()
	],
	concat: [
		StringType,
		varargs(ValueType),
		(ctx, args) => args.map((arg) => valueToString(arg.evaluate(ctx))).join("")
	],
	split: [
		array(StringType),
		[StringType, StringType],
		(ctx, [s, delim]) => s.evaluate(ctx).split(delim.evaluate(ctx))
	],
	join: [
		StringType,
		[array(StringType), StringType],
		(ctx, [arr, delim]) => arr.evaluate(ctx).join(delim.evaluate(ctx))
	],
	"resolved-locale": [
		StringType,
		[CollatorType],
		(ctx, [collator]) => collator.evaluate(ctx).resolvedLocale()
	]
});
function stringifySignature(signature) {
	if (Array.isArray(signature)) return `(${signature.map(typeToString).join(", ")})`;
	else return `(${typeToString(signature.type)}...)`;
}
function isExpressionConstant(expression) {
	if (expression instanceof Var) return isExpressionConstant(expression.boundExpression);
	else if (expression instanceof CompoundExpression && expression.name === "error") return false;
	else if (expression instanceof CollatorExpression) return false;
	else if (expression instanceof Within) return false;
	else if (expression instanceof Distance) return false;
	else if (expression instanceof GlobalState) return false;
	const isTypeAnnotation = expression instanceof Coercion || expression instanceof Assertion;
	let childrenConstant = true;
	expression.eachChild((child) => {
		if (isTypeAnnotation) childrenConstant = childrenConstant && isExpressionConstant(child);
		else childrenConstant = childrenConstant && child instanceof Literal;
	});
	if (!childrenConstant) return false;
	return isFeatureConstant(expression) && isGlobalPropertyConstant(expression, [
		"zoom",
		"heatmap-density",
		"elevation",
		"line-progress",
		"accumulated",
		"is-supported-script"
	]);
}
function isFeatureConstant(e) {
	if (e instanceof CompoundExpression) {
		if (e.name === "get" && e.args.length === 1) return false;
		else if (e.name === "feature-state") return false;
		else if (e.name === "has" && e.args.length === 1) return false;
		else if (e.name === "properties" || e.name === "geometry-type" || e.name === "id") return false;
		else if (/^filter-/.test(e.name)) return false;
	}
	if (e instanceof Within) return false;
	if (e instanceof Distance) return false;
	let result = true;
	e.eachChild((arg) => {
		if (result && !isFeatureConstant(arg)) result = false;
	});
	return result;
}
function isStateConstant(e) {
	if (e instanceof CompoundExpression) {
		if (e.name === "feature-state") return false;
	}
	let result = true;
	e.eachChild((arg) => {
		if (result && !isStateConstant(arg)) result = false;
	});
	return result;
}
function isGlobalPropertyConstant(e, properties) {
	if (e instanceof CompoundExpression && properties.indexOf(e.name) >= 0) return false;
	let result = true;
	e.eachChild((arg) => {
		if (result && !isGlobalPropertyConstant(arg, properties)) result = false;
	});
	return result;
}
//#endregion
export { CompoundExpression, isExpressionConstant, isFeatureConstant, isGlobalPropertyConstant, isStateConstant };

//# sourceMappingURL=compound_expression.mjs.map