import { ValidationError } from "../error/validation_error.mjs";
//#region src/validate/validate_constants.ts
function validateConstants(options) {
	const key = options.key;
	const constants = options.value;
	if (constants) return [new ValidationError(key, constants, "constants have been deprecated as of v8")];
	else return [];
}
//#endregion
export { validateConstants };

//# sourceMappingURL=validate_constants.mjs.map