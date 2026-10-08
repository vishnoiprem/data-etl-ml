//#region src/expression/types/resolved_image.ts
var ResolvedImage = class ResolvedImage {
	constructor(options) {
		this.name = options.name;
		this.available = options.available;
	}
	toString() {
		return this.name;
	}
	static fromString(name) {
		if (!name) return null;
		return new ResolvedImage({
			name,
			available: false
		});
	}
};
//#endregion
export { ResolvedImage };

//# sourceMappingURL=resolved_image.mjs.map