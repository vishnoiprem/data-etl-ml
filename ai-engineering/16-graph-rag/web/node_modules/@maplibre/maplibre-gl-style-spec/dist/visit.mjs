import v8_default from "./reference/v8.mjs";
//#region src/visit.ts
function getPropertyReference(propertyName) {
	for (let i = 0; i < v8_default.layout.length; i++) for (const key in v8_default[v8_default.layout[i]]) if (key === propertyName) return v8_default[v8_default.layout[i]][key];
	for (let i = 0; i < v8_default.paint.length; i++) for (const key in v8_default[v8_default.paint[i]]) if (key === propertyName) return v8_default[v8_default.paint[i]][key];
	return null;
}
function eachSource(style, callback) {
	for (const k in style.sources) callback(style.sources[k]);
}
function eachLayer(style, callback) {
	for (const layer of style.layers) callback(layer);
}
function eachProperty(style, options, callback) {
	function inner(layer, propertyType) {
		const properties = layer[propertyType];
		if (!properties) return;
		Object.keys(properties).forEach((key) => {
			callback({
				path: [
					layer.id,
					propertyType,
					key
				],
				key,
				value: properties[key],
				reference: getPropertyReference(key),
				set(x) {
					properties[key] = x;
				}
			});
		});
	}
	eachLayer(style, (layer) => {
		if (options.paint) inner(layer, "paint");
		if (options.layout) inner(layer, "layout");
	});
}
//#endregion
export { eachLayer, eachProperty, eachSource };

//# sourceMappingURL=visit.mjs.map