import { createExpression, findGlobalStateRefs } from "../expression/index.mjs";
//#region src/feature_filter/index.ts
function classifyChildren(children) {
	let sawLegacy = false;
	for (const child of children) {
		const classification = classifyFilter(child);
		if (classification === "expression") return "expression";
		if (classification === "legacy") sawLegacy = true;
	}
	return sawLegacy ? "legacy" : "neutral";
}
function classifyFilter(filter) {
	if (typeof filter === "boolean") return "neutral";
	if (!Array.isArray(filter) || filter.length === 0) return "legacy";
	switch (filter[0]) {
		case "has":
			if (filter.length < 2 || filter[1] === "$id" || filter[1] === "$type") return "legacy";
			return filter.length === 2 ? "neutral" : "expression";
		case "in": return filter.length >= 3 && (typeof filter[1] !== "string" || Array.isArray(filter[2])) ? "expression" : "legacy";
		case "!in":
		case "!has": return "legacy";
		case "==":
		case "!=":
		case ">":
		case ">=":
		case "<":
		case "<=": return filter.length !== 3 || Array.isArray(filter[1]) || Array.isArray(filter[2]) ? "expression" : "legacy";
		case "none": return "legacy";
		case "any":
		case "all": return classifyChildren(filter.slice(1));
		default: return "expression";
	}
}
function isExpressionFilter(filter) {
	return classifyFilter(filter) !== "legacy";
}
function getFilterPropertyExpression(property) {
	if (property === "$type") return ["geometry-type"];
	if (property === "$id") return ["id"];
	return ["get", property];
}
function getLegacyFilterExpressionSuggestion(filter) {
	switch (filter[0]) {
		case "==":
		case "!=":
		case "<":
		case "<=":
		case ">":
		case ">=":
			if (filter.length !== 3 || typeof filter[1] !== "string") return null;
			return [
				filter[0],
				getFilterPropertyExpression(filter[1]),
				filter[2]
			];
		case "in":
		case "!in": {
			if (filter.length < 2 || typeof filter[1] !== "string") return null;
			const expression = [
				"in",
				getFilterPropertyExpression(filter[1]),
				["literal", filter.slice(2)]
			];
			return filter[0] === "!in" ? ["!", expression] : expression;
		}
		case "has":
		case "!has": {
			if (filter.length !== 2 || typeof filter[1] !== "string") return null;
			if (filter[1] === "$type" || filter[1] === "$id") return null;
			const expression = ["has", filter[1]];
			return filter[0] === "!has" ? ["!", expression] : expression;
		}
		default: return null;
	}
}
function getMixedFilterMessage(filter) {
	if ((filter[0] === "<" || filter[0] === "<=" || filter[0] === ">" || filter[0] === ">=") && filter[1] === "$type") return `"$type" cannot be use with operator "${filter[0]}"`;
	const suggestion = getLegacyFilterExpressionSuggestion(filter);
	if (suggestion) return `Mixing deprecated filter syntax with expression syntax is not supported. Replace ${JSON.stringify(filter)} with ${JSON.stringify(suggestion)}.`;
	return `Mixing deprecated filter syntax with expression syntax is not supported. Convert ${JSON.stringify(filter)} to expression syntax.`;
}
function checkChild(index, path, filter) {
	const child = filter[index];
	if (!Array.isArray(child)) return null;
	if (!isExpressionFilter(child)) return {
		path: path.concat(index),
		legacyFilter: child
	};
	return findMixedLegacyFilter(child, path.concat(index));
}
function findMixedLegacyFilter(filter, path = []) {
	if (!Array.isArray(filter) || filter.length < 1) return null;
	switch (filter[0]) {
		case "all":
		case "any":
		case "none":
			for (let i = 1; i < filter.length; i++) {
				const diagnostic = checkChild(i, path, filter);
				if (diagnostic) return diagnostic;
			}
			break;
		case "!": {
			const diagnostic = checkChild(1, path, filter);
			if (diagnostic) return diagnostic;
			break;
		}
		case "case": for (let i = 1; i < filter.length - 1; i += 2) {
			const diagnostic = checkChild(i, path, filter);
			if (diagnostic) return diagnostic;
		}
	}
	return null;
}
function warnAboutMixedLegacyFilter(filter, rootKey) {
	const diagnostic = findMixedLegacyFilter(filter);
	if (!diagnostic || typeof console === "undefined") return;
	const path = diagnostic.path.map((index) => `[${index}]`).join("");
	console.warn(`${rootKey}${path}: ${getMixedFilterMessage(diagnostic.legacyFilter)}`);
}
const filterSpec = {
	type: "boolean",
	default: false,
	transition: false,
	"property-type": "data-driven",
	expression: {
		interpolated: false,
		parameters: ["zoom", "feature"]
	}
};
/**
* Given a filter expressed as nested arrays, return a new function
* that evaluates whether a given feature (with a .properties or .tags property)
* passes its test.
*
* @private
* @param filter MapLibre filter
* @param rootKey Location of the filter in the style JSON (e.g. `layers[3].filter`),
* used to prefix runtime warnings
* @param [globalState] Global state object to be used for evaluating 'global-state' expressions
* @returns filter-evaluating function
*/
function featureFilter(filter, rootKey, globalState) {
	if (filter === null || filter === void 0) return {
		filter: () => true,
		needGeometry: false,
		getGlobalStateRefs: () => /* @__PURE__ */ new Set()
	};
	if (!isExpressionFilter(filter)) filter = convertFilter(filter);
	else warnAboutMixedLegacyFilter(filter, rootKey);
	const compiled = createExpression(filter, rootKey, filterSpec, globalState);
	if (compiled.result === "error") throw new Error(compiled.value.map((err) => `${err.key}: ${err.message}`).join(", "));
	else return {
		filter: (globalProperties, feature, canonical) => compiled.value.evaluate(globalProperties, feature, {}, canonical),
		needGeometry: geometryNeeded(filter),
		getGlobalStateRefs: () => findGlobalStateRefs(compiled.value.expression)
	};
}
function compare(a, b) {
	return a < b ? -1 : a > b ? 1 : 0;
}
function geometryNeeded(filter) {
	if (!Array.isArray(filter)) return false;
	if (filter[0] === "within" || filter[0] === "distance") return true;
	for (let index = 1; index < filter.length; index++) if (geometryNeeded(filter[index])) return true;
	return false;
}
function convertFilter(filter) {
	if (!filter) return true;
	const op = filter[0];
	if (filter.length <= 1) return op !== "any";
	return op === "==" ? convertComparisonOp(filter[1], filter[2], "==") : op === "!=" ? convertNegation(convertComparisonOp(filter[1], filter[2], "==")) : op === "<" || op === ">" || op === "<=" || op === ">=" ? convertComparisonOp(filter[1], filter[2], op) : op === "any" ? convertDisjunctionOp(filter.slice(1)) : op === "all" ? ["all"].concat(filter.slice(1).map(convertFilter)) : op === "none" ? ["all"].concat(filter.slice(1).map(convertFilter).map(convertNegation)) : op === "in" ? convertInOp(filter[1], filter.slice(2)) : op === "!in" ? convertNegation(convertInOp(filter[1], filter.slice(2))) : op === "has" ? convertHasOp(filter[1]) : op === "!has" ? convertNegation(convertHasOp(filter[1])) : true;
}
function convertComparisonOp(property, value, op) {
	switch (property) {
		case "$type": return [`filter-type-${op}`, value];
		case "$id": return [`filter-id-${op}`, value];
		default: return [
			`filter-${op}`,
			property,
			value
		];
	}
}
function convertDisjunctionOp(filters) {
	return ["any"].concat(filters.map(convertFilter));
}
function convertInOp(property, values) {
	if (values.length === 0) return false;
	switch (property) {
		case "$type": return ["filter-type-in", ["literal", values]];
		case "$id": return ["filter-id-in", ["literal", values]];
		default: if (values.length > 200 && !values.some((v) => typeof v !== typeof values[0])) return [
			"filter-in-large",
			property,
			["literal", values.sort(compare)]
		];
		else return [
			"filter-in-small",
			property,
			["literal", values]
		];
	}
}
function convertHasOp(property) {
	switch (property) {
		case "$type": return true;
		case "$id": return ["filter-has-id"];
		default: return ["filter-has", property];
	}
}
function convertNegation(filter) {
	return ["!", filter];
}
//#endregion
export { featureFilter, findMixedLegacyFilter, getMixedFilterMessage, isExpressionFilter, warnAboutMixedLegacyFilter };

//# sourceMappingURL=index.mjs.map