import { latest } from "./reference/latest.mjs";
import { validateConstants } from "./validate/validate_constants.mjs";
import { validateFilter } from "./validate/validate_filter.mjs";
import { validatePaintProperty } from "./validate/validate_paint_property.mjs";
import { validateLayoutProperty } from "./validate/validate_layout_property.mjs";
import { validateLayer } from "./validate/validate_layer.mjs";
import { validateSource } from "./validate/validate_source.mjs";
import { validateLight } from "./validate/validate_light.mjs";
import { validateSky } from "./validate/validate_sky.mjs";
import { validateTerrain } from "./validate/validate_terrain.mjs";
import { validateSprite } from "./validate/validate_sprite.mjs";
import { validateState } from "./validate/validate_state.mjs";
import { validateFontFaces } from "./validate/validate_font_faces.mjs";
import { validate } from "./validate/validate.mjs";
import { validateGlyphsUrl } from "./validate/validate_glyphs_url.mjs";
//#region src/validate_style.min.ts
/**
* Validate a MapLibre style against the style specification.
* Use this when running in the browser.
*
* @param style - The style to be validated.
* @param styleSpec - The style specification to validate against.
* If omitted, the latest style spec is used.
* @returns an array of errors, or an empty array if no errors are found.
* @example
*   const validate = require('@maplibre/maplibre-gl-style-spec/').validateStyleMin;
*   const errors = validate(style);
*/
function validateStyleMin(style, styleSpec = latest) {
	let errors = [];
	errors = errors.concat(validate({
		key: "",
		value: style,
		valueSpec: styleSpec.$root,
		styleSpec,
		style,
		validateSpec: validate,
		objectElementValidators: {
			glyphs: validateGlyphsUrl,
			"*"() {
				return [];
			}
		}
	}));
	if (style["constants"]) errors = errors.concat(validateConstants({
		key: "constants",
		value: style["constants"],
		style,
		styleSpec,
		validateSpec: validate
	}));
	return sortErrors(errors);
}
validateStyleMin.source = wrapCleanErrors(injectValidateSpec(validateSource));
validateStyleMin.sprite = wrapCleanErrors(injectValidateSpec(validateSprite));
validateStyleMin.glyphs = wrapCleanErrors(injectValidateSpec(validateGlyphsUrl));
validateStyleMin.fontFaces = wrapCleanErrors(injectValidateSpec(validateFontFaces));
validateStyleMin.light = wrapCleanErrors(injectValidateSpec(validateLight));
validateStyleMin.sky = wrapCleanErrors(injectValidateSpec(validateSky));
validateStyleMin.terrain = wrapCleanErrors(injectValidateSpec(validateTerrain));
validateStyleMin.state = wrapCleanErrors(injectValidateSpec(validateState));
validateStyleMin.layer = wrapCleanErrors(injectValidateSpec(validateLayer));
validateStyleMin.filter = wrapCleanErrors(injectValidateSpec(validateFilter));
validateStyleMin.paintProperty = wrapCleanErrors(injectValidateSpec(validatePaintProperty));
validateStyleMin.layoutProperty = wrapCleanErrors(injectValidateSpec(validateLayoutProperty));
function injectValidateSpec(validator) {
	return function(options) {
		return validator(Object.assign({}, options, { validateSpec: validate }));
	};
}
function sortErrors(errors) {
	return [].concat(errors).sort((a, b) => {
		return a.line - b.line;
	});
}
function wrapCleanErrors(inner) {
	return function(...args) {
		return sortErrors(inner.apply(this, args));
	};
}
//#endregion
export { validateStyleMin };

//# sourceMappingURL=validate_style.min.mjs.map