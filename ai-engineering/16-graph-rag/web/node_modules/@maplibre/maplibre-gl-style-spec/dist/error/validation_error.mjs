//#region src/error/validation_error.ts
var ValidationError = class {
	constructor(key, value, message, identifier, severity = "error") {
		this.message = (key ? `${key}: ` : "") + message;
		if (identifier) this.identifier = identifier;
		this.severity = severity;
		if (value !== null && value !== void 0 && value.__line__) this.line = value.__line__;
	}
};
//#endregion
export { ValidationError };

//# sourceMappingURL=validation_error.mjs.map