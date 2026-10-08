import { ValidationError } from "../error/validation_error.mjs";
import { Color } from "../expression/types/color.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_color.ts
function validateColor(options) {
	const key = options.key;
	const value = options.value;
	const type = getType(value);
	if (type !== "string") return [new ValidationError(key, value, `color expected, ${type} found`)];
	if (!Color.parse(String(value))) return [new ValidationError(key, value, `color expected, "${value}" found`)];
	return [];
}
//#endregion
export { validateColor };

//# sourceMappingURL=validate_color.mjs.map