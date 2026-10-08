//#region src/util/get_own.ts
const hasOwnProperty = Object.hasOwn || function hasOwnProperty(object, key) {
	return Object.prototype.hasOwnProperty.call(object, key);
};
function getOwn(object, key) {
	return hasOwnProperty(object, key) ? object[key] : void 0;
}
//#endregion
export { getOwn };

//# sourceMappingURL=get_own.mjs.map