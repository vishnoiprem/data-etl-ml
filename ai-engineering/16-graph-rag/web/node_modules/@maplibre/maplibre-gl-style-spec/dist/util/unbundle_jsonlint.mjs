//#region src/util/unbundle_jsonlint.ts
function unbundle(value) {
	if (value instanceof Number || value instanceof String || value instanceof Boolean) return value.valueOf();
	else return value;
}
function deepUnbundle(value) {
	if (Array.isArray(value)) return value.map(deepUnbundle);
	else if (value instanceof Object && !(value instanceof Number || value instanceof String || value instanceof Boolean)) {
		const unbundledValue = {};
		for (const key in value) unbundledValue[key] = deepUnbundle(value[key]);
		return unbundledValue;
	}
	return unbundle(value);
}
//#endregion
export { deepUnbundle, unbundle };

//# sourceMappingURL=unbundle_jsonlint.mjs.map