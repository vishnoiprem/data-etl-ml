import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { validateNumber } from "./validate_number.mjs";
//#region src/validate/validate_padding.ts
function validatePadding(options) {
	const key = options.key;
	const value = options.value;
	if (getType(value) === "array") {
		if (value.length < 1 || value.length > 4) return [new ValidationError(key, value, `padding requires 1 to 4 values; ${value.length} values found`)];
		const arrayElementSpec = { type: "number" };
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
export { validatePadding };

//# sourceMappingURL=validate_padding.mjs.map