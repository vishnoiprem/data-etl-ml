import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_string.ts
function validateString(options) {
	const value = options.value;
	const key = options.key;
	const type = getType(value);
	if (type !== "string") return [new ValidationError(key, value, `string expected, ${type} found`)];
	return [];
}
//#endregion
export { validateString };

//# sourceMappingURL=validate_string.mjs.map