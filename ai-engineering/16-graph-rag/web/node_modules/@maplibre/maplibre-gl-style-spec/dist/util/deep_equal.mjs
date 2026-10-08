//#region src/util/deep_equal.ts
/**
* Deeply compares two object literals.
*
* @private
*/
function deepEqual(a, b) {
	if (Array.isArray(a)) {
		if (!Array.isArray(b) || a.length !== b.length) return false;
		for (let i = 0; i < a.length; i++) if (!deepEqual(a[i], b[i])) return false;
		return true;
	}
	if (typeof a === "object" && a !== null && b !== null) {
		if (!(typeof b === "object")) return false;
		if (Object.keys(a).length !== Object.keys(b).length) return false;
		for (const key in a) if (!deepEqual(a[key], b[key])) return false;
		return true;
	}
	return a === b;
}
//#endregion
export { deepEqual };

//# sourceMappingURL=deep_equal.mjs.map