import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { validateColor } from "./validate_color.mjs";
//#region src/validate/validate_color_array.ts
function validateColorArray(options) {
	const key = options.key;
	const value = options.value;
	if (getType(value) === "array") {
		if (value.length < 1) return [new ValidationError(key, value, "array length at least 1 expected, length 0 found")];
		let errors = [];
		for (let i = 0; i < value.length; i++) errors = errors.concat(validateColor({
			key: `${key}[${i}]`,
			value: value[i],
			valueSpec: {}
		}));
		return errors;
	} else return validateColor({
		key,
		value,
		valueSpec: {}
	});
}
//#endregion
export { validateColorArray };

//# sourceMappingURL=validate_color_array.mjs.map