import { ValidationError } from "../error/validation_error.mjs";
import { validateString } from "./validate_string.mjs";
//#region src/validate/validate_glyphs_url.ts
function validateGlyphsUrl(options) {
	const value = options.value;
	const key = options.key;
	const errors = validateString(options);
	if (errors.length) return errors;
	if (value.indexOf("{fontstack}") === -1) errors.push(new ValidationError(key, value, "\"glyphs\" url must include a \"{fontstack}\" token"));
	if (value.indexOf("{range}") === -1) errors.push(new ValidationError(key, value, "\"glyphs\" url must include a \"{range}\" token"));
	return errors;
}
//#endregion
export { validateGlyphsUrl };

//# sourceMappingURL=validate_glyphs_url.mjs.map