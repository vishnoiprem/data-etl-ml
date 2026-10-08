import { eachLayer, eachProperty, eachSource } from "../visit.mjs";
//#region src/migrate/v8.ts
function eachLayout(layer, callback) {
	for (const k in layer) if (k.indexOf("layout") === 0) callback(layer[k], k);
}
function eachPaint(layer, callback) {
	for (const k in layer) if (k.indexOf("paint") === 0) callback(layer[k], k);
}
function resolveConstant(style, value) {
	if (typeof value === "string" && value[0] === "@") return resolveConstant(style, style.constants[value]);
	else return value;
}
function isFunction(value) {
	return Array.isArray(value.stops);
}
function renameProperty(obj, from, to) {
	obj[to] = obj[from];
	delete obj[from];
}
function migrateV8(style) {
	style.version = 8;
	eachSource(style, (source) => {
		if (source.type === "video" && source["url"] !== void 0) renameProperty(source, "url", "urls");
		if (source.type === "video") source.coordinates.forEach((coord) => {
			return coord.reverse();
		});
	});
	eachLayer(style, (layer) => {
		eachLayout(layer, (layout) => {
			if (layout["symbol-min-distance"] !== void 0) renameProperty(layout, "symbol-min-distance", "symbol-spacing");
		});
		eachPaint(layer, (paint) => {
			if (paint["background-image"] !== void 0) renameProperty(paint, "background-image", "background-pattern");
			if (paint["line-image"] !== void 0) renameProperty(paint, "line-image", "line-pattern");
			if (paint["fill-image"] !== void 0) renameProperty(paint, "fill-image", "fill-pattern");
		});
	});
	eachProperty(style, {
		paint: true,
		layout: true
	}, (property) => {
		const value = resolveConstant(style, property.value);
		if (isFunction(value)) value.stops.forEach((stop) => {
			stop[1] = resolveConstant(style, stop[1]);
		});
		property.set(value);
	});
	delete style["constants"];
	eachLayer(style, (layer) => {
		eachLayout(layer, (layout) => {
			delete layout["text-max-size"];
			delete layout["icon-max-size"];
		});
		eachPaint(layer, (paint) => {
			if (paint["text-size"]) {
				if (!layer.layout) layer.layout = {};
				layer.layout["text-size"] = paint["text-size"];
				delete paint["text-size"];
			}
			if (paint["icon-size"]) {
				if (!layer.layout) layer.layout = {};
				layer.layout["icon-size"] = paint["icon-size"];
				delete paint["icon-size"];
			}
		});
	});
	function migrateFontStack(font) {
		function splitAndTrim(string) {
			return string.split(",").map((s) => {
				return s.trim();
			});
		}
		if (Array.isArray(font)) return font;
		else if (typeof font === "string") return splitAndTrim(font);
		else if (typeof font === "object") {
			font.stops.forEach((stop) => {
				stop[1] = splitAndTrim(stop[1]);
			});
			return font;
		} else throw new Error("unexpected font value");
	}
	eachLayer(style, (layer) => {
		eachLayout(layer, (layout) => {
			if (layout["text-font"]) layout["text-font"] = migrateFontStack(layout["text-font"]);
		});
	});
	let firstSymbolLayer = 0;
	for (let i = style.layers.length - 1; i >= 0; i--) if (style.layers[i].type !== "symbol") {
		firstSymbolLayer = i + 1;
		break;
	}
	const symbolLayers = style.layers.splice(firstSymbolLayer);
	symbolLayers.reverse();
	style.layers = style.layers.concat(symbolLayers);
	return style;
}
//#endregion
export { migrateV8 };

//# sourceMappingURL=v8.mjs.map