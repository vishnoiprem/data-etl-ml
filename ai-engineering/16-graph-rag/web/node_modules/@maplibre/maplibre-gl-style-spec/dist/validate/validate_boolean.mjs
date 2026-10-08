import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_boolean.ts
function validateBoolean(options) {
	const value = options.value;
	const key = options.key;
	const type = getType(value);
	if (type !== "boolean") return [new ValidationError(key, value, `boolean expected, ${type} found`)];
	return [];
}
//#endregion
export { validateBoolean };

//# sourceMappingURL=validate_boolean.mjs.map