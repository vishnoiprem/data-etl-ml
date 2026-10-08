//#region src/expression/runtime_error.ts
var RuntimeError = class extends Error {
	constructor(message, path) {
		super(message);
		this.name = "RuntimeError";
		this.path = path;
	}
	toJSON() {
		return this.message;
	}
};
//#endregion
export { RuntimeError };

//# sourceMappingURL=runtime_error.mjs.map