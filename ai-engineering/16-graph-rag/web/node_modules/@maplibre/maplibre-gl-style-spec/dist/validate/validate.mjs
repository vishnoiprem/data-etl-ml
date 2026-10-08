import { extendBy } from "../util/extend.mjs";
import { isFunction } from "../function/index.mjs";
import { isExpression } from "../expression/index.mjs";
import { validateConstants } from "./validate_constants.mjs";
import { deepUnbundle, unbundle } from "../util/unbundle_jsonlint.mjs";
import { validateObject } from "./validate_object.mjs";
import { validateArray } from "./validate_array.mjs";
import { validateNumber } from "./validate_number.mjs";
import { validateFunction } from "./validate_function.mjs";
import { validateExpression } from "./validate_expression.mjs";
import { validateBoolean } from "./validate_boolean.mjs";
import { validateColor } from "./validate_color.mjs";
import { validateEnum } from "./validate_enum.mjs";
import { validateFilter } from "./validate_filter.mjs";
import { validateLayer } from "./validate_layer.mjs";
import { validateString } from "./validate_string.mjs";
import { validateSource } from "./validate_source.mjs";
import { validateLight } from "./validate_light.mjs";
import { validateSky } from "./validate_sky.mjs";
import { validateTerrain } from "./validate_terrain.mjs";
import { validateFormatted } from "./validate_formatted.mjs";
import { validateImage } from "./validate_image.mjs";
import { validatePadding } from "./validate_padding.mjs";
import { validateNumberArray } from "./validate_number_array.mjs";
import { validateColorArray } from "./validate_color_array.mjs";
import { validateVariableAnchorOffsetCollection } from "./validate_variable_anchor_offset_collection.mjs";
import { validateSprite } from "./validate_sprite.mjs";
import { validateProjection } from "./validate_projection.mjs";
import { validateProjectionDefinition } from "./validate_projectiondefinition.mjs";
import { validateState } from "./validate_state.mjs";
import { validateFontFaces } from "./validate_font_faces.mjs";
//#region src/validate/validate.ts
const VALIDATORS = {
	"*"() {
		return [];
	},
	array: validateArray,
	boolean: validateBoolean,
	number: validateNumber,
	color: validateColor,
	constants: validateConstants,
	enum: validateEnum,
	filter: validateFilter,
	function: validateFunction,
	layer: validateLayer,
	object: validateObject,
	source: validateSource,
	light: validateLight,
	sky: validateSky,
	terrain: validateTerrain,
	projection: validateProjection,
	projectionDefinition: validateProjectionDefinition,
	string: validateString,
	formatted: validateFormatted,
	resolvedImage: validateImage,
	padding: validatePadding,
	numberArray: validateNumberArray,
	colorArray: validateColorArray,
	variableAnchorOffsetCollection: validateVariableAnchorOffsetCollection,
	sprite: validateSprite,
	state: validateState,
	fontFaces: validateFontFaces
};
/**
* Main recursive validation function used internally.
* You should use `validateStyleMin` in the browser or `validateStyle` in node env.
* @param options - the options object
* @param options.key - string representing location of validation in style tree. Used only
* for more informative error reporting.
* @param options.value - current value from style being evaluated. May be anything from a
* high level object that needs to be descended into deeper or a simple
* scalar value.
* @param options.valueSpec - current spec being evaluated. Tracks value.
* @param options.styleSpec - current full spec being evaluated.
* @param options.validateSpec - the validate function itself
* @param options.style - the style object
* @param options.objectElementValidators - optional object of functions that will be called
* @returns an array of errors, or an empty array if no errors are found.
*/
function validate(options) {
	const value = options.value;
	const valueSpec = options.valueSpec;
	const styleSpec = options.styleSpec;
	options.validateSpec = validate;
	if (valueSpec.expression && isFunction(unbundle(value))) return validateFunction(options);
	else if (valueSpec.expression && isExpression(deepUnbundle(value))) return validateExpression(options);
	else if (valueSpec.type && VALIDATORS[valueSpec.type]) return VALIDATORS[valueSpec.type](options);
	else return validateObject(extendBy({}, options, { valueSpec: valueSpec.type ? styleSpec[valueSpec.type] : valueSpec }));
}
//#endregion
export { validate };

//# sourceMappingURL=validate.mjs.map