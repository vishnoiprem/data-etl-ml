import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { isObjectLiteral } from "../util/is_object_literal.mjs";
//#region src/validate/validate_state.ts
function validateState(options) {
	if (!isObjectLiteral(options.value)) return [new ValidationError(options.key, options.value, `object expected, ${getType(options.value)} found`)];
	return [];
}
//#endregion
export { validateState };

//# sourceMappingURL=validate_state.mjs.map