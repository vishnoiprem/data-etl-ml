//#region src/util/is_object_literal.ts
function isObjectLiteral(anything) {
	return Boolean(anything) && anything.constructor === Object;
}
//#endregion
export { isObjectLiteral };

//# sourceMappingURL=is_object_literal.mjs.map