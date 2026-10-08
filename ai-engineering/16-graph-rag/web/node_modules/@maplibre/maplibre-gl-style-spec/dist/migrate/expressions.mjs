import { isExpression } from "../expression/index.mjs";
import { convertFilter } from "../feature_filter/convert.mjs";
import { convertFunction, convertTokenString } from "../function/convert.mjs";
import { eachLayer, eachProperty } from "../visit.mjs";
//#region src/migrate/expressions.ts
/**
* Migrate the given style object in place to use expressions. Specifically,
* this will convert (a) "stop" functions, and (b) legacy filters to their
* expression equivalents.
* @param style The style object to migrate.
* @returns The migrated style object.
*/
function expressions(style) {
	const converted = [];
	eachLayer(style, (layer) => {
		if (layer.filter) layer.filter = convertFilter(layer.filter);
	});
	eachProperty(style, {
		paint: true,
		layout: true
	}, ({ path, key, value, reference, set }) => {
		if (isExpression(value) || key.endsWith("-transition") || reference === null) return;
		if (typeof value === "object" && !Array.isArray(value)) {
			set(convertFunction(value, reference));
			converted.push(path.join("."));
		} else if (reference.tokens && typeof value === "string") set(convertTokenString(value));
	});
	return style;
}
//#endregion
export { expressions };

//# sourceMappingURL=expressions.mjs.map