//#region src/util/interpolate-primitives.ts
function interpolateNumber(from, to, t) {
	return from + t * (to - from);
}
function interpolateArray(from, to, t) {
	return from.map((d, i) => {
		return interpolateNumber(d, to[i], t);
	});
}
//#endregion
export { interpolateArray, interpolateNumber };

//# sourceMappingURL=interpolate-primitives.mjs.map