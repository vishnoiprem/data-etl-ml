import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { validateNumber } from "./validate_number.mjs";
//#region src/validate/validate_number_array.ts
function validateNumberArray(options) {
	const key = options.key;
	const value = options.value;
	if (getType(value) === "array") {
		const arrayElementSpec = { type: "number" };
		if (value.length < 1) return [new ValidationError(key, value, "array length at least 1 expected, length 0 found")];
		let errors = [];
		for (let i = 0; i < value.length; i++) errors = errors.concat(options.validateSpec({
			key: `${key}[${i}]`,
			value: value[i],
			validateSpec: options.validateSpec,
			valueSpec: arrayElementSpec
		}));
		return errors;
	} else return validateNumber({
		key,
		value,
		valueSpec: {}
	});
}
//#endregion
export { validateNumberArray };

//# sourceMappingURL=validate_number_array.mjs.map