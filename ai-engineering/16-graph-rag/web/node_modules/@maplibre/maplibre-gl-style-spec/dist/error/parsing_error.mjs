//#region src/error/parsing_error.ts
var ParsingError = class {
	constructor(error) {
		this.error = error;
		this.message = error.message;
		const match = error.message.match(/line (\d+)/);
		this.line = match ? parseInt(match[1], 10) : 0;
	}
};
//#endregion
export { ParsingError };

//# sourceMappingURL=parsing_error.mjs.map