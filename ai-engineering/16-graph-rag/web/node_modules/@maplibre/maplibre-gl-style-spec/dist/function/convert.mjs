//#region src/function/convert.ts
function convertLiteral(value) {
	return typeof value === "object" ? ["literal", value] : value;
}
function convertFunction(parameters, propertySpec) {
	let stops = parameters.stops;
	if (!stops) return convertIdentityFunction(parameters, propertySpec);
	const zoomAndFeatureDependent = stops && typeof stops[0][0] === "object";
	const featureDependent = zoomAndFeatureDependent || parameters.property !== void 0;
	const zoomDependent = zoomAndFeatureDependent || !featureDependent;
	stops = stops.map((stop) => {
		if (!featureDependent && propertySpec.tokens && typeof stop[1] === "string") return [stop[0], convertTokenString(stop[1])];
		return [stop[0], convertLiteral(stop[1])];
	});
	if (zoomAndFeatureDependent) return convertZoomAndPropertyFunction(parameters, propertySpec, stops);
	else if (zoomDependent) return convertZoomFunction(parameters, propertySpec, stops);
	else return convertPropertyFunction(parameters, propertySpec, stops);
}
function convertIdentityFunction(parameters, propertySpec) {
	const get = ["get", parameters.property];
	if (parameters.default === void 0) return propertySpec.type === "string" ? ["string", get] : get;
	else if (propertySpec.type === "enum") return [
		"match",
		get,
		Object.keys(propertySpec.values),
		get,
		parameters.default
	];
	else {
		const expression = [
			propertySpec.type === "color" ? "to-color" : propertySpec.type,
			get,
			convertLiteral(parameters.default)
		];
		if (propertySpec.type === "array") expression.splice(1, 0, propertySpec.value, propertySpec.length || null);
		return expression;
	}
}
function getInterpolateOperator(parameters) {
	switch (parameters.colorSpace) {
		case "hcl": return "interpolate-hcl";
		case "lab": return "interpolate-lab";
		default: return "interpolate";
	}
}
function convertZoomAndPropertyFunction(parameters, propertySpec, stops) {
	const featureFunctionParameters = {};
	const featureFunctionStops = {};
	const zoomStops = [];
	for (let s = 0; s < stops.length; s++) {
		const stop = stops[s];
		const zoom = stop[0].zoom;
		if (featureFunctionParameters[zoom] === void 0) {
			featureFunctionParameters[zoom] = {
				zoom,
				type: parameters.type,
				property: parameters.property,
				default: parameters.default
			};
			featureFunctionStops[zoom] = [];
			zoomStops.push(zoom);
		}
		featureFunctionStops[zoom].push([stop[0].value, stop[1]]);
	}
	if (getFunctionType({}, propertySpec) === "exponential") {
		const expression = [
			getInterpolateOperator(parameters),
			["linear"],
			["zoom"]
		];
		for (const z of zoomStops) appendStopPair(expression, z, convertPropertyFunction(featureFunctionParameters[z], propertySpec, featureFunctionStops[z]), false);
		return expression;
	} else {
		const expression = ["step", ["zoom"]];
		for (const z of zoomStops) appendStopPair(expression, z, convertPropertyFunction(featureFunctionParameters[z], propertySpec, featureFunctionStops[z]), true);
		fixupDegenerateStepCurve(expression);
		return expression;
	}
}
function coalesce(a, b) {
	if (a !== void 0) return a;
	if (b !== void 0) return b;
}
function getFallback(parameters, propertySpec) {
	const defaultValue = convertLiteral(coalesce(parameters.default, propertySpec.default));
	if (defaultValue === void 0 && propertySpec.type === "resolvedImage") return "";
	return defaultValue;
}
function convertPropertyFunction(parameters, propertySpec, stops) {
	const type = getFunctionType(parameters, propertySpec);
	const get = ["get", parameters.property];
	if (type === "categorical" && typeof stops[0][0] === "boolean") {
		const expression = ["case"];
		for (const stop of stops) expression.push([
			"==",
			get,
			stop[0]
		], stop[1]);
		expression.push(getFallback(parameters, propertySpec));
		return expression;
	} else if (type === "categorical") {
		const expression = ["match", get];
		for (const stop of stops) appendStopPair(expression, stop[0], stop[1], false);
		expression.push(getFallback(parameters, propertySpec));
		return expression;
	} else if (type === "interval") {
		const expression = ["step", ["number", get]];
		for (const stop of stops) appendStopPair(expression, stop[0], stop[1], true);
		fixupDegenerateStepCurve(expression);
		return parameters.default === void 0 ? expression : [
			"case",
			[
				"==",
				["typeof", get],
				"number"
			],
			expression,
			convertLiteral(parameters.default)
		];
	} else if (type === "exponential") {
		const base = parameters.base !== void 0 ? parameters.base : 1;
		const expression = [
			getInterpolateOperator(parameters),
			base === 1 ? ["linear"] : ["exponential", base],
			["number", get]
		];
		for (const stop of stops) appendStopPair(expression, stop[0], stop[1], false);
		return parameters.default === void 0 ? expression : [
			"case",
			[
				"==",
				["typeof", get],
				"number"
			],
			expression,
			convertLiteral(parameters.default)
		];
	} else throw new Error(`Unknown property function type ${type}`);
}
function convertZoomFunction(parameters, propertySpec, stops, input = ["zoom"]) {
	const type = getFunctionType(parameters, propertySpec);
	let expression;
	let isStep = false;
	if (type === "interval") {
		expression = ["step", input];
		isStep = true;
	} else if (type === "exponential") {
		const base = parameters.base !== void 0 ? parameters.base : 1;
		expression = [
			getInterpolateOperator(parameters),
			base === 1 ? ["linear"] : ["exponential", base],
			input
		];
	} else throw new Error(`Unknown zoom function type "${type}"`);
	for (const stop of stops) appendStopPair(expression, stop[0], stop[1], isStep);
	fixupDegenerateStepCurve(expression);
	return expression;
}
function fixupDegenerateStepCurve(expression) {
	if (expression[0] === "step" && expression.length === 3) {
		expression.push(0);
		expression.push(expression[3]);
	}
}
function appendStopPair(curve, input, output, isStep) {
	if (curve.length > 3 && input === curve[curve.length - 2]) return;
	if (!(isStep && curve.length === 2)) curve.push(input);
	curve.push(output);
}
function getFunctionType(parameters, propertySpec) {
	if (parameters.type) return parameters.type;
	else return propertySpec.expression.interpolated ? "exponential" : "interval";
}
function convertTokenString(s) {
	const result = ["concat"];
	const re = /{([^{}]+)}/g;
	let pos = 0;
	for (let match = re.exec(s); match !== null; match = re.exec(s)) {
		const literal = s.slice(pos, re.lastIndex - match[0].length);
		pos = re.lastIndex;
		if (literal.length > 0) result.push(literal);
		result.push(["get", match[1]]);
	}
	if (result.length === 1) return s;
	if (pos < s.length) result.push(s.slice(pos));
	else if (result.length === 2) return ["to-string", result[1]];
	return result;
}
//#endregion
export { convertFunction, convertTokenString };

//# sourceMappingURL=convert.mjs.map