import { isExpressionFilter } from "./index.mjs";
//#region src/feature_filter/convert.ts
function convertFilter(filter, expectedTypes = {}) {
	if (isExpressionFilter(filter)) return filter;
	if (!filter) return true;
	const legacyFilter = filter;
	const legacyOp = legacyFilter[0];
	if (filter.length <= 1) return legacyOp !== "any";
	switch (legacyOp) {
		case "==":
		case "!=":
		case "<":
		case ">":
		case "<=":
		case ">=": {
			const [, property, value] = filter;
			return convertComparisonOp(property, value, legacyOp, expectedTypes);
		}
		case "any": {
			const [, ...conditions] = legacyFilter;
			return ["any", ...conditions.map((f) => {
				const types = {};
				const child = convertFilter(f, types);
				const typechecks = runtimeTypeChecks(types);
				return typechecks === true ? child : [
					"case",
					typechecks,
					child,
					false
				];
			})];
		}
		case "all": {
			const [, ...conditions] = legacyFilter;
			const children = conditions.map((f) => convertFilter(f, expectedTypes));
			return children.length > 1 ? ["all", ...children] : children[0];
		}
		case "none": {
			const [, ...conditions] = legacyFilter;
			return ["!", convertFilter(["any", ...conditions], {})];
		}
		case "in": {
			const [, property, ...values] = legacyFilter;
			return convertInOp(property, values);
		}
		case "!in": {
			const [, property, ...values] = legacyFilter;
			return convertInOp(property, values, true);
		}
		case "has": return convertHasOp(legacyFilter[1]);
		case "!has": return ["!", convertHasOp(legacyFilter[1])];
		default: return true;
	}
}
function runtimeTypeChecks(expectedTypes) {
	const conditions = [];
	for (const property in expectedTypes) {
		const get = property === "$id" ? ["id"] : ["get", property];
		conditions.push([
			"==",
			["typeof", get],
			expectedTypes[property]
		]);
	}
	if (conditions.length === 0) return true;
	if (conditions.length === 1) return conditions[0];
	return ["all", ...conditions];
}
function convertComparisonOp(property, value, op, expectedTypes) {
	let get;
	if (property === "$type") return [
		op,
		["geometry-type"],
		value
	];
	else if (property === "$id") get = ["id"];
	else get = ["get", property];
	if (expectedTypes && value !== null) expectedTypes[property] = typeof value;
	if (op === "==" && property !== "$id" && value === null) return [
		"all",
		["has", property],
		[
			"==",
			get,
			null
		]
	];
	else if (op === "!=" && property !== "$id" && value === null) return [
		"any",
		["!", ["has", property]],
		[
			"!=",
			get,
			null
		]
	];
	return [
		op,
		get,
		value
	];
}
function convertInOp(property, values, negate = false) {
	if (values.length === 0) return negate;
	let get;
	if (property === "$type") get = ["geometry-type"];
	else if (property === "$id") get = ["id"];
	else get = ["get", property];
	let uniformTypes = true;
	const type = typeof values[0];
	for (const value of values) if (typeof value !== type) {
		uniformTypes = false;
		break;
	}
	if (uniformTypes && (type === "string" || type === "number")) {
		const uniqueValues = values.sort().filter((v, i) => i === 0 || values[i - 1] !== v);
		return [
			"match",
			get,
			uniqueValues,
			!negate,
			negate
		];
	}
	if (negate) return ["all", ...values.map((v) => [
		"!=",
		get,
		v
	])];
	else return ["any", ...values.map((v) => [
		"==",
		get,
		v
	])];
}
function convertHasOp(property) {
	if (property === "$type") return true;
	else if (property === "$id") return [
		"!=",
		["id"],
		null
	];
	else return ["has", property];
}
//#endregion
export { convertFilter };

//# sourceMappingURL=convert.mjs.map