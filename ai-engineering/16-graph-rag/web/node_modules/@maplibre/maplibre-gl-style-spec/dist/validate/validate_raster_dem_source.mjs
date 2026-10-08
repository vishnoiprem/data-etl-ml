import { ValidationError } from "../error/validation_error.mjs";
import { getType } from "../util/get_type.mjs";
import { unbundle } from "../util/unbundle_jsonlint.mjs";
//#region src/validate/validate_raster_dem_source.ts
function validateRasterDEMSource(options) {
	const sourceName = options.sourceName ?? "";
	const rasterDEM = options.value;
	const styleSpec = options.styleSpec;
	const rasterDEMSpec = styleSpec.source_raster_dem;
	const style = options.style;
	let errors = [];
	const rootType = getType(rasterDEM);
	if (rasterDEM === void 0) return errors;
	else if (rootType !== "object") {
		errors.push(new ValidationError("source_raster_dem", rasterDEM, `object expected, ${rootType} found`));
		return errors;
	}
	const isCustomEncoding = unbundle(rasterDEM.encoding) === "custom";
	const customEncodingKeys = [
		"redFactor",
		"greenFactor",
		"blueFactor",
		"baseShift"
	];
	const encodingName = options.value.encoding ? `"${options.value.encoding}"` : "Default";
	for (const key in rasterDEM) if (!isCustomEncoding && customEncodingKeys.includes(key)) errors.push(new ValidationError(key, rasterDEM[key], `In "${sourceName}": "${key}" is only valid when "encoding" is set to "custom". ${encodingName} encoding found`));
	else if (rasterDEMSpec[key]) errors = errors.concat(options.validateSpec({
		key,
		value: rasterDEM[key],
		valueSpec: rasterDEMSpec[key],
		validateSpec: options.validateSpec,
		style,
		styleSpec
	}));
	else errors.push(new ValidationError(key, rasterDEM[key], `unknown property "${key}"`));
	return errors;
}
//#endregion
export { validateRasterDEMSource };

//# sourceMappingURL=validate_raster_dem_source.mjs.map