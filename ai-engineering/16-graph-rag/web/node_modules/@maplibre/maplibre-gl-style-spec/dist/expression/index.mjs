import { ExpressionParsingError } from "./parsing_error.mjs";
import { BooleanType, ColorArrayType, ColorType, FormattedType, NumberArrayType, NumberType, PaddingType, ProjectionDefinitionType, ResolvedImageType, StringType, ValueType, VariableAnchorOffsetCollectionType, array } from "./types.mjs";
import { Color } from "./types/color.mjs";
import { Padding } from "./types/padding.mjs";
import { NumberArray } from "./types/number_array.mjs";
import { ColorArray } from "./types/color_array.mjs";
import { RuntimeError } from "./runtime_error.mjs";
import { VariableAnchorOffsetCollection } from "./types/variable_anchor_offset_collection.mjs";
import { ProjectionDefinition } from "./types/projection_definition.mjs";
import { EvaluationContext } from "./evaluation_context.mjs";
import { ParsingContext } from "./parsing_context.mjs";
import { Let } from "./definitions/let.mjs";
import { Step } from "./definitions/step.mjs";
import { Interpolate } from "./definitions/interpolate.mjs";
import { Coalesce } from "./definitions/coalesce.mjs";
import { GlobalState } from "./definitions/global_state.mjs";
import { expressions } from "./definitions/index.mjs";
import { CompoundExpression, isExpressionConstant, isFeatureConstant, isGlobalPropertyConstant, isStateConstant } from "./compound_expression.mjs";
import { error, success } from "../util/result.mjs";
import { supportsInterpolation, supportsPropertyExpression, supportsZoomExpression } from "../util/properties.mjs";
import { createFunction, isFunction } from "../function/index.mjs";
//#region src/expression/index.ts
var StyleExpression = class {
	constructor(expression, rootKey, propertySpec, globalState) {
		this.expression = expression;
		this._warningHistory = {};
		this._evaluator = new EvaluationContext();
		this._defaultValue = propertySpec ? getDefaultValue(propertySpec) : null;
		this._enumValues = propertySpec && propertySpec.type === "enum" ? propertySpec.values : null;
		this._globalState = globalState;
		this._rootKey = rootKey;
	}
	evaluateWithoutErrorHandling(globals, feature, featureState, canonical, availableImages, formattedSection) {
		if (this._globalState) globals = addGlobalState(globals, this._globalState);
		this._evaluator.globals = globals;
		this._evaluator.feature = feature;
		this._evaluator.featureState = featureState;
		this._evaluator.canonical = canonical;
		this._evaluator.availableImages = availableImages || null;
		this._evaluator.formattedSection = formattedSection;
		return this.expression.evaluate(this._evaluator);
	}
	evaluate(globals, feature, featureState, canonical, availableImages, formattedSection) {
		if (this._globalState) globals = addGlobalState(globals, this._globalState);
		this._evaluator.globals = globals;
		this._evaluator.feature = feature || null;
		this._evaluator.featureState = featureState || null;
		this._evaluator.canonical = canonical;
		this._evaluator.availableImages = availableImages || null;
		this._evaluator.formattedSection = formattedSection || null;
		try {
			const val = this.expression.evaluate(this._evaluator);
			if (val === null || val === void 0 || typeof val === "number" && val !== val) return this._defaultValue;
			if (this._enumValues && !(val in this._enumValues)) throw new RuntimeError(`Expected value to be one of ${Object.keys(this._enumValues).map((v) => JSON.stringify(v)).join(", ")}, but found ${JSON.stringify(val)} instead.`, "");
			return val;
		} catch (e) {
			const path = e instanceof RuntimeError ? e.path : "";
			const dedupKey = `${path}|${e.message}`;
			if (!this._warningHistory[dedupKey]) {
				this._warningHistory[dedupKey] = true;
				if (typeof console !== "undefined") console.warn(formatRuntimeWarning(this._rootKey, path, e.message, this._defaultValue));
			}
			return this._defaultValue;
		}
	}
};
/**
* Builds the warning logged when an expression or legacy function fails at
* evaluation: a `rootKey + index path` location prefix, plus the fallback
* value being used.
* @param rootKey Caller-supplied location of the expression in the style JSON
* @param path Index path of the throwing sub-expression ('' for the root)
* @param message The error message from the failed evaluation
* @param defaultValue The value being fallen back to
* @returns The formatted warning string
*/
function formatRuntimeWarning(rootKey, path, message, defaultValue) {
	return `${rootKey}${path}: ${message}${defaultValue == null ? "" : ` Falling back to ${String(defaultValue)}.`}`;
}
/**
* Rejects a missing or empty root key. The location prefix is what makes
* runtime warnings actionable, so callers must always supply one; failing
* here surfaces the programmer error at style load instead of producing
* unattributable warnings at render time.
* @param rootKey The root key to check
*/
function assertRootKey(rootKey) {
	if (!rootKey) throw new Error("rootKey must identify the location of the expression in the style JSON, e.g. \"layers[3].paint.line-width\".");
}
function isExpression(expression) {
	return Array.isArray(expression) && expression.length > 0 && typeof expression[0] === "string" && expression[0] in expressions;
}
/**
* Parse and typecheck the given style spec JSON expression.  If
* options.defaultValue is provided, then the resulting StyleExpression's
* `evaluate()` method will handle errors by logging a warning (once per
* message) and returning the default value.  Otherwise, it will throw
* evaluation errors.
*
* @private
*/
function createExpression(expression, rootKey, propertySpec, globalState) {
	assertRootKey(rootKey);
	const parser = new ParsingContext(expressions, isExpressionConstant, [], propertySpec ? getExpectedType(propertySpec) : void 0);
	const parsed = parser.parse(expression, void 0, void 0, void 0, propertySpec && propertySpec.type === "string" ? { typeAnnotation: "coerce" } : void 0);
	if (!parsed) return error(parser.errors);
	return success(new StyleExpression(parsed, rootKey, propertySpec, globalState));
}
var ZoomConstantExpression = class {
	constructor(kind, expression, globalState) {
		this.kind = kind;
		this._styleExpression = expression;
		this.isStateDependent = kind !== "constant" && !isStateConstant(expression.expression);
		this.globalStateRefs = findGlobalStateRefs(expression.expression);
		this._globalState = globalState;
	}
	evaluateWithoutErrorHandling(globals, feature, featureState, canonical, availableImages, formattedSection) {
		if (this._globalState) globals = addGlobalState(globals, this._globalState);
		return this._styleExpression.evaluateWithoutErrorHandling(globals, feature, featureState, canonical, availableImages, formattedSection);
	}
	evaluate(globals, feature, featureState, canonical, availableImages, formattedSection) {
		if (this._globalState) globals = addGlobalState(globals, this._globalState);
		return this._styleExpression.evaluate(globals, feature, featureState, canonical, availableImages, formattedSection);
	}
};
var ZoomDependentExpression = class {
	constructor(kind, expression, zoomStops, interpolationType, globalState) {
		this.kind = kind;
		this.zoomStops = zoomStops;
		this._styleExpression = expression;
		this.isStateDependent = kind !== "camera" && !isStateConstant(expression.expression);
		this.globalStateRefs = findGlobalStateRefs(expression.expression);
		this.interpolationType = interpolationType;
		this._globalState = globalState;
	}
	evaluateWithoutErrorHandling(globals, feature, featureState, canonical, availableImages, formattedSection) {
		if (this._globalState) globals = addGlobalState(globals, this._globalState);
		return this._styleExpression.evaluateWithoutErrorHandling(globals, feature, featureState, canonical, availableImages, formattedSection);
	}
	evaluate(globals, feature, featureState, canonical, availableImages, formattedSection) {
		if (this._globalState) globals = addGlobalState(globals, this._globalState);
		return this._styleExpression.evaluate(globals, feature, featureState, canonical, availableImages, formattedSection);
	}
	interpolationFactor(input, lower, upper) {
		if (this.interpolationType) return Interpolate.interpolationFactor(this.interpolationType, input, lower, upper);
		else return 0;
	}
};
function isZoomExpression(expression) {
	return expression._styleExpression !== void 0;
}
function createPropertyExpression(expressionInput, rootKey, propertySpec, globalState) {
	const expression = createExpression(expressionInput, rootKey, propertySpec, globalState);
	if (expression.result === "error") return expression;
	const parsed = expression.value.expression;
	const isFeatureConstantResult = isFeatureConstant(parsed);
	if (!isFeatureConstantResult && !supportsPropertyExpression(propertySpec)) return error([new ExpressionParsingError("", "data expressions not supported")]);
	const isZoomConstant = isGlobalPropertyConstant(parsed, ["zoom"]);
	if (!isZoomConstant && !supportsZoomExpression(propertySpec)) return error([new ExpressionParsingError("", "zoom expressions not supported")]);
	const zoomCurve = findZoomCurve(parsed);
	if (!zoomCurve && !isZoomConstant) return error([new ExpressionParsingError("", "\"zoom\" expression may only be used as input to a top-level \"step\" or \"interpolate\" expression.")]);
	else if (zoomCurve instanceof ExpressionParsingError) return error([zoomCurve]);
	else if (zoomCurve instanceof Interpolate && !supportsInterpolation(propertySpec)) return error([new ExpressionParsingError("", "\"interpolate\" expressions cannot be used with this property")]);
	if (!zoomCurve) return success(isFeatureConstantResult ? new ZoomConstantExpression("constant", expression.value, globalState) : new ZoomConstantExpression("source", expression.value, globalState));
	const interpolationType = zoomCurve instanceof Interpolate ? zoomCurve.interpolation : void 0;
	return success(isFeatureConstantResult ? new ZoomDependentExpression("camera", expression.value, zoomCurve.labels, interpolationType, globalState) : new ZoomDependentExpression("composite", expression.value, zoomCurve.labels, interpolationType, globalState));
}
var StylePropertyFunction = class StylePropertyFunction {
	constructor(parameters, rootKey, specification) {
		this.isStateDependent = false;
		this.globalStateRefs = /* @__PURE__ */ new Set();
		this._globalState = null;
		assertRootKey(rootKey);
		this._parameters = parameters;
		this._specification = specification;
		this._rootKey = rootKey;
		this._defaultValue = getDefaultValue(specification);
		this._warningHistory = {};
		const fn = createFunction(this._parameters, this._specification);
		this.kind = fn.kind;
		this.interpolationFactor = fn.interpolationFactor;
		this.zoomStops = fn.zoomStops;
		this.interpolationType = fn.interpolationType;
		this._innerEvaluate = fn.evaluate;
	}
	/**
	* Evaluates the legacy function, handling a runtime throw (e.g. interpolating
	* mismatched value types) by warning with the property location and falling
	* back to the spec default, mirroring {@link StyleExpression.evaluate}.
	* @param globals Global evaluation properties (e.g. zoom)
	* @param feature The feature being evaluated, if any
	* @returns The function result, or the spec default if evaluation throws
	*/
	evaluate(globals, feature) {
		try {
			return this._innerEvaluate(globals, feature);
		} catch (e) {
			const message = e instanceof Error ? e.message : String(e);
			const dedupKey = `|${message}`;
			if (!this._warningHistory[dedupKey]) {
				this._warningHistory[dedupKey] = true;
				if (typeof console !== "undefined") console.warn(formatRuntimeWarning(this._rootKey, "", message, this._defaultValue));
			}
			return this._defaultValue;
		}
	}
	static deserialize(serialized) {
		return new StylePropertyFunction(serialized._parameters, serialized._rootKey, serialized._specification);
	}
	static serialize(input) {
		return {
			_parameters: input._parameters,
			_specification: input._specification,
			_rootKey: input._rootKey
		};
	}
};
function normalizePropertyExpression(value, rootKey, specification, globalState) {
	if (isFunction(value)) return new StylePropertyFunction(value, rootKey, specification);
	else if (isExpression(value)) {
		const expression = createPropertyExpression(value, rootKey, specification, globalState);
		if (expression.result === "error") throw new Error(expression.value.map((err) => `${err.key}: ${err.message}`).join(", "));
		return expression.value;
	} else {
		let constant = value;
		if (specification.type === "color" && typeof value === "string") constant = Color.parse(value);
		else if (specification.type === "padding" && (typeof value === "number" || Array.isArray(value))) constant = Padding.parse(value);
		else if (specification.type === "numberArray" && (typeof value === "number" || Array.isArray(value))) constant = NumberArray.parse(value);
		else if (specification.type === "colorArray" && (typeof value === "string" || Array.isArray(value))) constant = ColorArray.parse(value);
		else if (specification.type === "variableAnchorOffsetCollection" && Array.isArray(value)) constant = VariableAnchorOffsetCollection.parse(value);
		else if (specification.type === "projectionDefinition" && typeof value === "string") constant = ProjectionDefinition.parse(value);
		return {
			globalStateRefs: /* @__PURE__ */ new Set(),
			_globalState: null,
			kind: "constant",
			evaluate: () => constant
		};
	}
}
function findZoomCurve(expression) {
	let result = null;
	if (expression instanceof Let) result = findZoomCurve(expression.result);
	else if (expression instanceof Coalesce) for (const arg of expression.args) {
		result = findZoomCurve(arg);
		if (result) break;
	}
	else if ((expression instanceof Step || expression instanceof Interpolate) && expression.input instanceof CompoundExpression && expression.input.name === "zoom") result = expression;
	if (result instanceof ExpressionParsingError) return result;
	expression.eachChild((child) => {
		const childResult = findZoomCurve(child);
		if (childResult instanceof ExpressionParsingError) result = childResult;
		else if (!result && childResult) result = new ExpressionParsingError("", "\"zoom\" expression may only be used as input to a top-level \"step\" or \"interpolate\" expression.");
		else if (result && childResult && result !== childResult) result = new ExpressionParsingError("", "Only one zoom-based \"step\" or \"interpolate\" subexpression may be used in an expression.");
	});
	return result;
}
function findGlobalStateRefs(expression, results = /* @__PURE__ */ new Set()) {
	if (expression instanceof GlobalState) results.add(expression.key);
	expression.eachChild((childExpression) => {
		findGlobalStateRefs(childExpression, results);
	});
	return results;
}
function getExpectedType(spec) {
	const types = {
		color: ColorType,
		string: StringType,
		number: NumberType,
		enum: StringType,
		boolean: BooleanType,
		formatted: FormattedType,
		padding: PaddingType,
		numberArray: NumberArrayType,
		colorArray: ColorArrayType,
		projectionDefinition: ProjectionDefinitionType,
		resolvedImage: ResolvedImageType,
		variableAnchorOffsetCollection: VariableAnchorOffsetCollectionType
	};
	if (spec.type === "array") return array(types[spec.value] || ValueType, spec.length);
	return types[spec.type];
}
function getDefaultValue(spec) {
	if (spec.type === "color" && isFunction(spec.default)) return new Color(0, 0, 0, 0);
	switch (spec.type) {
		case "color": return Color.parse(spec.default) || null;
		case "padding": return Padding.parse(spec.default) || null;
		case "numberArray": return NumberArray.parse(spec.default) || null;
		case "colorArray": return ColorArray.parse(spec.default) || null;
		case "variableAnchorOffsetCollection": return VariableAnchorOffsetCollection.parse(spec.default) || null;
		case "projectionDefinition": return ProjectionDefinition.parse(spec.default) || null;
		default: return spec.default === void 0 ? null : spec.default;
	}
}
function addGlobalState(globals, globalState) {
	const { zoom, heatmapDensity, elevation, lineProgress, isSupportedScript, accumulated } = globals ?? {};
	return {
		zoom,
		heatmapDensity,
		elevation,
		lineProgress,
		isSupportedScript,
		accumulated,
		globalState
	};
}
//#endregion
export { StyleExpression, StylePropertyFunction, ZoomConstantExpression, ZoomDependentExpression, createExpression, createPropertyExpression, findGlobalStateRefs, isExpression, isZoomExpression, normalizePropertyExpression };

//# sourceMappingURL=index.mjs.map