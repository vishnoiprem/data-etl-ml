import v8_default from "../reference/v8.mjs";
import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { validateObject } from "./validate_object.mjs";
import { validateString } from "./validate_string.mjs";
import { isObjectLiteral } from "../util/is_object_literal.mjs";
//#region src/validate/validate_font_faces.ts
const MAX_CODE_POINT = 1114111;
/**
* A single unicode range, as described by the [CSS descriptor with the same name](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/unicode-range):
* a single code point (`U+26`), a range of code points (`U+0-7F`) or a wildcard range (`U+4??`).
* At most six hexadecimal digits are allowed on either side.
*/
const UNICODE_RANGE_REGEX = /^u\+(?:([0-9a-f]{1,6})(?:-([0-9a-f]{1,6}))?|([0-9a-f]{0,5}\?{1,6}))$/i;
function validateUnicodeRange(key, value) {
	if (getType(value) !== "string") return [];
	const range = `${value}`;
	const invalid = () => [new ValidationError(key, value, `invalid unicode range, expected a value such as "U+26", "U+0-10FFFF" or "U+4??"`)];
	const match = range.match(UNICODE_RANGE_REGEX);
	if (!match) return invalid();
	const [, start, end, wildcard] = match;
	if (wildcard !== void 0) return wildcard.length > 6 ? invalid() : [];
	const startCodePoint = parseInt(start, 16);
	const endCodePoint = end === void 0 ? startCodePoint : parseInt(end, 16);
	if (startCodePoint > MAX_CODE_POINT || endCodePoint > MAX_CODE_POINT) return [new ValidationError(key, value, `unicode range is out of bounds, the maximum code point is U+10FFFF`)];
	if (startCodePoint > endCodePoint) return [new ValidationError(key, value, `unicode range start must not be greater than its end, but ${range} is`)];
	return [];
}
function validateFontFaces(options) {
	const key = options.key ?? "font-faces";
	const value = options.value;
	const validateSpec = options.validateSpec;
	const styleSpec = options.styleSpec ?? v8_default;
	const style = options.style;
	if (!isObjectLiteral(value)) return [new ValidationError(key, value, `object expected, ${getType(value)} found`)];
	const errors = [];
	for (const fontName in value) {
		const fontValue = value[fontName];
		const fontValueType = getType(fontValue);
		if (fontValueType === "string") errors.push(...validateString({
			key: `${key}.${fontName}`,
			value: fontValue
		}));
		else if (fontValueType === "array") {
			const fontFaceSpec = {
				url: {
					type: "string",
					required: true
				},
				"unicode-range": {
					type: "array",
					value: "string"
				}
			};
			for (const [i, fontFace] of fontValue.entries()) {
				const fontFaceKey = `${key}.${fontName}[${i}]`;
				errors.push(...validateObject({
					key: fontFaceKey,
					value: fontFace,
					valueSpec: fontFaceSpec,
					styleSpec,
					style,
					validateSpec
				}));
				const unicodeRanges = isObjectLiteral(fontFace) ? fontFace["unicode-range"] : void 0;
				if (getType(unicodeRanges) !== "array") continue;
				for (const [j, unicodeRange] of unicodeRanges.entries()) errors.push(...validateUnicodeRange(`${fontFaceKey}.unicode-range[${j}]`, unicodeRange));
			}
		} else errors.push(new ValidationError(`${key}.${fontName}`, fontValue, `string or array expected, ${fontValueType} found`));
	}
	return errors;
}
//#endregion
export { validateFontFaces };

//# sourceMappingURL=validate_font_faces.mjs.map