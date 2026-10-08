import { ValidationError } from "../error/validation_error.mjs";
import { extendBy } from "../util/extend.mjs";
import { getType } from "../util/get_type.mjs";
import { unbundle } from "../util/unbundle_jsonlint.mjs";
import { validateObject } from "./validate_object.mjs";
import { validateFilter } from "./validate_filter.mjs";
import { validatePaintProperty } from "./validate_paint_property.mjs";
import { validateLayoutProperty } from "./validate_layout_property.mjs";
//#region src/validate/validate_layer.ts
function validateLayer(options) {
	let errors = [];
	const layer = options.value;
	const key = options.key;
	const style = options.style;
	const styleSpec = options.styleSpec;
	if (getType(layer) !== "object") return [new ValidationError(key, layer, `object expected, ${getType(layer)} found`)];
	if (!layer.type && !layer.ref) errors.push(new ValidationError(key, layer, "either \"type\" or \"ref\" is required"));
	let type = unbundle(layer.type);
	const ref = unbundle(layer.ref);
	if (layer.id) {
		const layerId = unbundle(layer.id);
		for (let i = 0; i < options.arrayIndex; i++) {
			const otherLayer = style.layers[i];
			if (unbundle(otherLayer.id) === layerId) errors.push(new ValidationError(key, layer.id, `duplicate layer id "${layer.id}", previously used at line ${otherLayer.id.__line__}`));
		}
	}
	if ("ref" in layer) {
		[
			"type",
			"source",
			"source-layer",
			"filter",
			"layout"
		].forEach((p) => {
			if (p in layer) errors.push(new ValidationError(key, layer[p], `"${p}" is prohibited for ref layers`));
		});
		let parent;
		style.layers.forEach((layer) => {
			if (unbundle(layer.id) === ref) parent = layer;
		});
		if (!parent) errors.push(new ValidationError(key, layer.ref, `ref layer "${ref}" not found`));
		else if (parent.ref) errors.push(new ValidationError(key, layer.ref, "ref cannot reference another ref layer"));
		else type = unbundle(parent.type);
	} else if (type !== "background") {
		if (!layer.source) errors.push(new ValidationError(key, layer, "missing required property \"source\""));
		else {
			const source = style.sources && style.sources[layer.source];
			const sourceType = source && unbundle(source.type);
			if (!source) errors.push(new ValidationError(key, layer.source, `source "${layer.source}" not found`));
			else if (sourceType === "vector" && type === "raster") errors.push(new ValidationError(key, layer.source, `layer "${layer.id}" requires a raster source`));
			else if (sourceType !== "raster-dem" && type === "hillshade") errors.push(new ValidationError(key, layer.source, `layer "${layer.id}" requires a raster-dem source`));
			else if (sourceType !== "raster-dem" && type === "color-relief") errors.push(new ValidationError(key, layer.source, `layer "${layer.id}" requires a raster-dem source`));
			else if (sourceType === "raster" && type !== "raster") errors.push(new ValidationError(key, layer.source, `layer "${layer.id}" requires a vector source`));
			else if (sourceType === "vector" && !layer["source-layer"]) errors.push(new ValidationError(key, layer, `layer "${layer.id}" must specify a "source-layer"`));
			else if (sourceType === "raster-dem" && type !== "hillshade" && type !== "color-relief") errors.push(new ValidationError(key, layer.source, "raster-dem source can only be used with layer type 'hillshade' or 'color-relief'."));
			else if (type === "line" && layer.paint && layer.paint["line-gradient"] && (sourceType !== "geojson" || !source.lineMetrics)) errors.push(new ValidationError(key, layer, `layer "${layer.id}" specifies a line-gradient, which requires a GeoJSON source with \`lineMetrics\` enabled.`));
		}
	}
	if (type === "raster" && layer.paint?.resampling && layer.paint?.["raster-resampling"]) errors.push(new ValidationError(key, layer.paint, `layer "${layer.id}" redundantly specifies "resampling" and "raster-resampling" paint properties, but only one is allowed. It is advised to use "resampling".`));
	errors = errors.concat(validateObject({
		key,
		value: layer,
		valueSpec: styleSpec.layer,
		style: options.style,
		styleSpec: options.styleSpec,
		validateSpec: options.validateSpec,
		objectElementValidators: {
			"*"() {
				return [];
			},
			type() {
				return options.validateSpec({
					key: `${key}.type`,
					value: layer.type,
					valueSpec: styleSpec.layer.type,
					style: options.style,
					styleSpec: options.styleSpec,
					validateSpec: options.validateSpec,
					object: layer,
					objectKey: "type"
				});
			},
			filter: validateFilter,
			layout(options) {
				return validateObject({
					layer,
					key: options.key,
					value: options.value,
					style: options.style,
					styleSpec: options.styleSpec,
					validateSpec: options.validateSpec,
					objectElementValidators: { "*"(options) {
						return validateLayoutProperty(extendBy({ layerType: type }, options));
					} }
				});
			},
			paint(options) {
				return validateObject({
					layer,
					key: options.key,
					value: options.value,
					style: options.style,
					styleSpec: options.styleSpec,
					validateSpec: options.validateSpec,
					objectElementValidators: { "*"(options) {
						return validatePaintProperty(extendBy({ layerType: type }, options));
					} }
				});
			}
		}
	}));
	return errors;
}
//#endregion
export { validateLayer };

//# sourceMappingURL=validate_layer.mjs.map