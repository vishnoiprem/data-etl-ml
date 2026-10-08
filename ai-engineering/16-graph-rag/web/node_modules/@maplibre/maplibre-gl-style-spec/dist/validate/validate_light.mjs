import { ValidationError } from "../error/validation_error.mjs";
import { transitionPropertyRegExp } from "../util/properties.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_light.ts
function validateLight(options) {
	const light = options.value;
	const styleSpec = options.styleSpec;
	const lightSpec = styleSpec.light;
	const style = options.style;
	let errors = [];
	const rootType = getType(light);
	if (light === void 0) return errors;
	else if (rootType !== "object") {
		errors = errors.concat([new ValidationError("light", light, `object expected, ${rootType} found`)]);
		return errors;
	}
	for (const key in light) {
		const transitionMatch = key.match(transitionPropertyRegExp);
		if (transitionMatch && lightSpec[transitionMatch[1]] && lightSpec[transitionMatch[1]].transition) errors = errors.concat(options.validateSpec({
			key,
			value: light[key],
			valueSpec: styleSpec.transition,
			validateSpec: options.validateSpec,
			style,
			styleSpec
		}));
		else if (lightSpec[key]) errors = errors.concat(options.validateSpec({
			key,
			value: light[key],
			valueSpec: lightSpec[key],
			validateSpec: options.validateSpec,
			style,
			styleSpec
		}));
		else errors = errors.concat([new ValidationError(key, light[key], `unknown property "${key}"`)]);
	}
	return errors;
}
//#endregion
export { validateLight };

//# sourceMappingURL=validate_light.mjs.map