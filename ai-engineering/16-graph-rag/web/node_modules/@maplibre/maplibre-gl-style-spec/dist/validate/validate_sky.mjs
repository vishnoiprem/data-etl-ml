import { ValidationError } from "../error/validation_error.mjs";
import { transitionPropertyRegExp } from "../util/properties.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_sky.ts
function validateSky(options) {
	const sky = options.value;
	const styleSpec = options.styleSpec;
	const skySpec = styleSpec.sky;
	const style = options.style;
	const rootType = getType(sky);
	if (sky === void 0) return [];
	else if (rootType !== "object") return [new ValidationError("sky", sky, `object expected, ${rootType} found`)];
	let errors = [];
	for (const key in sky) {
		const transitionMatch = key.match(transitionPropertyRegExp);
		if (transitionMatch && skySpec[transitionMatch[1]] && skySpec[transitionMatch[1]].transition) errors = errors.concat(options.validateSpec({
			key,
			value: sky[key],
			valueSpec: styleSpec.transition,
			style,
			styleSpec
		}));
		else if (skySpec[key]) errors = errors.concat(options.validateSpec({
			key,
			value: sky[key],
			valueSpec: skySpec[key],
			style,
			styleSpec
		}));
		else errors = errors.concat([new ValidationError(key, sky[key], `unknown property "${key}"`)]);
	}
	return errors;
}
//#endregion
export { validateSky };

//# sourceMappingURL=validate_sky.mjs.map