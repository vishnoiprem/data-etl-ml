import { validateExpression } from "./validate_expression.mjs";
import { validateString } from "./validate_string.mjs";
//#region src/validate/validate_image.ts
function validateImage(options) {
	if (validateString(options).length === 0) return [];
	return validateExpression(options);
}
//#endregion
export { validateImage };

//# sourceMappingURL=validate_image.mjs.map