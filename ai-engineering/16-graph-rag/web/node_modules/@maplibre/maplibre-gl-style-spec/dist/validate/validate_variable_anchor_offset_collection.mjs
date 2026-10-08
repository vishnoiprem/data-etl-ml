import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { validateArray } from "./validate_array.mjs";
import { validateEnum } from "./validate_enum.mjs";
//#region src/validate/validate_variable_anchor_offset_collection.ts
function validateVariableAnchorOffsetCollection(options) {
	const key = options.key;
	const value = options.value;
	const type = getType(value);
	const styleSpec = options.styleSpec;
	if (type !== "array" || value.length < 1 || value.length % 2 !== 0) return [new ValidationError(key, value, "variableAnchorOffsetCollection requires a non-empty array of even length")];
	let errors = [];
	for (let i = 0; i < value.length; i += 2) {
		errors = errors.concat(validateEnum({
			key: `${key}[${i}]`,
			value: value[i],
			valueSpec: styleSpec["layout_symbol"]["text-anchor"]
		}));
		errors = errors.concat(validateArray({
			key: `${key}[${i + 1}]`,
			value: value[i + 1],
			valueSpec: {
				length: 2,
				value: "number"
			},
			validateSpec: options.validateSpec,
			style: options.style,
			styleSpec
		}));
	}
	return errors;
}
//#endregion
export { validateVariableAnchorOffsetCollection };

//# sourceMappingURL=validate_variable_anchor_offset_collection.mjs.map