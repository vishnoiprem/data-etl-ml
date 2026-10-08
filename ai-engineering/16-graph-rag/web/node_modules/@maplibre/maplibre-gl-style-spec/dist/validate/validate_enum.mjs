import { ValidationError } from "../error/validation_error.mjs";
import { unbundle } from "../util/unbundle_jsonlint.mjs";
//#region src/validate/validate_enum.ts
function validateEnum(options) {
	const key = options.key;
	const value = options.value;
	const valueSpec = options.valueSpec;
	const errors = [];
	if (Array.isArray(valueSpec.values)) {
		if (valueSpec.values.indexOf(unbundle(value)) === -1) errors.push(new ValidationError(key, value, `expected one of [${valueSpec.values.join(", ")}], ${JSON.stringify(value)} found`));
	} else if (Object.keys(valueSpec.values).indexOf(unbundle(value)) === -1) errors.push(new ValidationError(key, value, `expected one of [${Object.keys(valueSpec.values).join(", ")}], ${JSON.stringify(value)} found`));
	return errors;
}
//#endregion
export { validateEnum };

//# sourceMappingURL=validate_enum.mjs.map