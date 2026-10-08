import { PbfWriter } from "pbf";
import Point from "@mapbox/point-geometry";
//#region lib/geojson_wrapper.ts
var FeatureWrapper = class {
	constructor(feature, extent) {
		this.feature = feature;
		this.type = feature.type;
		this.properties = feature.tags ? feature.tags : {};
		this.extent = extent;
		if ("id" in feature) {
			if (typeof feature.id === "string") this.id = parseInt(feature.id, 10);
			else if (typeof feature.id === "number" && !isNaN(feature.id)) this.id = feature.id;
		}
	}
	loadGeometry() {
		const geometry = [];
		const rawGeo = this.feature.type === 1 ? [this.feature.geometry] : this.feature.geometry;
		for (const ring of rawGeo) {
			const newRing = [];
			for (const point of ring) newRing.push(new Point(point[0], point[1]));
			geometry.push(newRing);
		}
		return geometry;
	}
};
const GEOJSON_TILE_LAYER_NAME = "_geojsonTileLayer";
var GeoJSONWrapper = class {
	constructor(features, options) {
		this.layers = { [GEOJSON_TILE_LAYER_NAME]: this };
		this.name = GEOJSON_TILE_LAYER_NAME;
		this.version = options ? options.version : 1;
		this.extent = options ? options.extent : 4096;
		this.length = features.length;
		this.features = features;
	}
	feature(i) {
		return new FeatureWrapper(this.features[i], this.extent);
	}
};
//#endregion
//#region index.ts
/**
* Serialize a vector-tile-js-created tile to pbf
*
* @param tile - the tile to serialize
* @param jsonPrefix - a string prefix to prepend to JSON-stringified non-primitive property values, used to distinguish them from regular string values when parsing the tile later. Default is "".
* @return uncompressed, pbf-serialized tile data
*/
function fromVectorTileJs(tile, jsonPrefix = "") {
	const out = new PbfWriter();
	writeTile(tile, out, jsonPrefix);
	return out.finish();
}
/**
* Serialized a geojson-vt-created tile to pbf.
*
* @param layers - An object mapping layer names to geojson-vt-created vector tile objects
* @param options - An object specifying the vector-tile specification version and extent that were used to create `layers`.
* @return uncompressed, pbf-serialized tile data
*/
function fromGeojsonVt(layers, options) {
	const l = {};
	for (const k in layers) {
		l[k] = new GeoJSONWrapper(layers[k].features, options);
		l[k].name = k;
		l[k].version = options ? options.version : 1;
		l[k].extent = options ? options.extent : 4096;
	}
	return fromVectorTileJs({ layers: l });
}
function writeTile(tile, pbf, jsonPrefix = "") {
	for (const key in tile.layers) pbf.writeMessage(3, (layer, pbf) => writeLayer(layer, pbf, jsonPrefix), tile.layers[key]);
}
function writeLayer(layer, pbf, jsonPrefix = "") {
	pbf.writeVarintField(15, layer.version || 1);
	pbf.writeStringField(1, layer.name || "");
	pbf.writeVarintField(5, layer.extent || 4096);
	const context = {
		jsonPrefix,
		keys: [],
		values: [],
		keycache: {},
		valuecache: {}
	};
	for (let i = 0; i < layer.length; i++) {
		context.feature = layer.feature(i);
		pbf.writeMessage(2, writeFeature, context);
	}
	const keys = context.keys;
	for (const key of keys) pbf.writeStringField(3, key);
	const values = context.values;
	for (const value of values) pbf.writeMessage(4, writeValue, value);
}
function writeFeature(context, pbf) {
	if (!context.feature) return;
	const feature = context.feature;
	if (feature.id !== void 0) pbf.writeVarintField(1, feature.id);
	pbf.writeMessage(2, writeProperties, context);
	pbf.writeVarintField(3, feature.type);
	pbf.writeMessage(4, writeGeometry, feature);
}
function writeProperties(context, pbf) {
	for (const key in context.feature?.properties) {
		let value = context.feature.properties[key];
		let keyIndex = context.keycache[key];
		if (value == null) continue;
		if (typeof keyIndex === "undefined") {
			context.keys.push(key);
			keyIndex = context.keys.length - 1;
			context.keycache[key] = keyIndex;
		}
		pbf.writeVarint(keyIndex);
		if (typeof value !== "string" && typeof value !== "boolean" && typeof value !== "number") value = context.jsonPrefix + JSON.stringify(value);
		const valueKey = typeof value + ":" + value;
		let valueIndex = context.valuecache[valueKey];
		if (typeof valueIndex === "undefined") {
			context.values.push(value);
			valueIndex = context.values.length - 1;
			context.valuecache[valueKey] = valueIndex;
		}
		pbf.writeVarint(valueIndex);
	}
}
function command(cmd, length) {
	return (length << 3) + (cmd & 7);
}
function zigzag(num) {
	return num << 1 ^ num >> 31;
}
function writeGeometry(feature, pbf) {
	const geometry = feature.loadGeometry();
	const type = feature.type;
	let x = 0;
	let y = 0;
	for (const ring of geometry) {
		let count = 1;
		if (type === 1) count = ring.length;
		pbf.writeVarint(command(1, count));
		const lineCount = type === 3 ? ring.length - 1 : ring.length;
		for (let i = 0; i < lineCount; i++) {
			if (i === 1 && type !== 1) pbf.writeVarint(command(2, lineCount - 1));
			const dx = ring[i].x - x;
			const dy = ring[i].y - y;
			pbf.writeVarint(zigzag(dx));
			pbf.writeVarint(zigzag(dy));
			x += dx;
			y += dy;
		}
		if (feature.type === 3) pbf.writeVarint(command(7, 1));
	}
}
function writeValue(value, pbf) {
	const type = typeof value;
	if (type === "string") pbf.writeStringField(1, value);
	else if (type === "boolean") pbf.writeBooleanField(7, value);
	else if (type === "number") if (value % 1 !== 0) pbf.writeDoubleField(3, value);
	else if (value < 0) pbf.writeSVarintField(6, value);
	else pbf.writeVarintField(5, value);
}
//#endregion
export { GEOJSON_TILE_LAYER_NAME, GeoJSONWrapper, fromGeojsonVt, fromVectorTileJs };

//# sourceMappingURL=index.es.js.map