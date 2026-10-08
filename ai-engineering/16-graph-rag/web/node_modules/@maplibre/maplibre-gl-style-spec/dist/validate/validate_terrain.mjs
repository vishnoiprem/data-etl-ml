import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_terrain.ts
function validateTerrain(options) {
	const terrain = options.value;
	const styleSpec = options.styleSpec;
	const terrainSpec = styleSpec.terrain;
	const style = options.style;
	let errors = [];
	const rootType = getType(terrain);
	if (terrain === void 0) return errors;
	else if (rootType !== "object") {
		errors = errors.concat([new ValidationError("terrain", terrain, `object expected, ${rootType} found`)]);
		return errors;
	}
	for (const key in terrain) if (terrainSpec[key]) errors = errors.concat(options.validateSpec({
		key,
		value: terrain[key],
		valueSpec: terrainSpec[key],
		validateSpec: options.validateSpec,
		style,
		styleSpec
	}));
	else errors = errors.concat([new ValidationError(key, terrain[key], `unknown property "${key}"`)]);
	return errors;
}
//#endregion
export { validateTerrain };

//# sourceMappingURL=validate_terrain.mjs.map