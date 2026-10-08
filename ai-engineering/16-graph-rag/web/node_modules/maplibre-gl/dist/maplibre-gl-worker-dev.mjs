/**
* MapLibre GL JS
* @license 3-Clause BSD. Full text of license: https://github.com/maplibre/maplibre-gl-js/blob/v6.11.2/LICENSE.txt
*/
import { An as addProtocol, Br as EXTENT, D as clipGeometry, Dt as RGBAImage, Et as AlphaImage, F as potpack, Fn as isAbortError, G as GeoJSONVT, H as rtlWorkerPlugin, Ir as warnOnce, Ln as JSON_PREFIX, Mn as removeProtocol, N as ImageAtlas, On as makeRequest, Tn as getJSON, Ui as Point, Vt as CollisionBoxArray, _ as createStyleLayer, bt as DEMData, c as GeoJSONWrapper, d as OverscaledTileID, dn as createExpression, dr as isImageBitmap, dt as VectorTile, en as EvaluationParameters, g as Actor, gr as isWorker, i as MLTVectorTile, l as fromVectorTileJs, ln as groupByLayout, lr as getImageData, nn as register, o as DictionaryCoder, r as FeatureIndex, rr as extend, t as BoundedLRUCache, tr as ensureError, un as featureFilter, vr as mapObject, wn as getArrayBuffer, z as PbfReader } from "./maplibre-gl-shared-dev.mjs";
//#region src/style/style_layer_index.ts
var StyleLayerIndex = class {
	constructor(layerConfigs, globalState) {
		this.keyCache = {};
		if (layerConfigs) this.replace(layerConfigs, globalState);
	}
	replace(layerConfigs, globalState) {
		this._layerConfigs = {};
		this._layers = {};
		this.update(layerConfigs, [], globalState);
	}
	update(layerConfigs, removedIds, globalState) {
		for (const layerConfig of layerConfigs) {
			this._layerConfigs[layerConfig.id] = layerConfig;
			const layer = this._layers[layerConfig.id] = createStyleLayer(layerConfig, globalState);
			layer._featureFilter = featureFilter(layer.filter, `layers[${layerConfig.id}].filter`, globalState);
			if (this.keyCache[layerConfig.id]) delete this.keyCache[layerConfig.id];
		}
		for (const id of removedIds) {
			delete this.keyCache[id];
			delete this._layerConfigs[id];
			delete this._layers[id];
		}
		this.familiesBySource = {};
		const groups = groupByLayout(Object.values(this._layerConfigs), this.keyCache);
		for (const layerConfigs of groups) {
			const layers = layerConfigs.map((layerConfig) => this._layers[layerConfig.id]);
			const layer = layers[0];
			if (layer.isHidden()) continue;
			const sourceId = layer.source || "";
			let sourceGroup = this.familiesBySource[sourceId];
			sourceGroup ||= this.familiesBySource[sourceId] = {};
			const sourceLayerId = layer.sourceLayer || "_geojsonTileLayer";
			let sourceLayerFamilies = sourceGroup[sourceLayerId];
			sourceLayerFamilies ||= sourceGroup[sourceLayerId] = [];
			sourceLayerFamilies.push(layers);
		}
	}
};
//#endregion
//#region src/render/glyph_atlas.ts
const padding = 1;
var GlyphAtlas = class {
	constructor(stacks) {
		const positions = {};
		const bins = [];
		for (const stack in stacks) {
			const stackPositions = positions[stack] = {};
			for (const variant in stacks[stack]) {
				const glyphs = stacks[stack][variant];
				stackPositions[variant] = {};
				for (const id in glyphs) {
					const src = glyphs[id];
					if (!src || src.bitmap.width === 0 || src.bitmap.height === 0) continue;
					const bin = {
						x: 0,
						y: 0,
						w: src.bitmap.width + 2,
						h: src.bitmap.height + 2
					};
					bins.push(bin);
					stackPositions[variant][id] = {
						rect: bin,
						metrics: src.metrics
					};
				}
			}
		}
		const { w, h } = potpack(bins);
		const image = new AlphaImage({
			width: w || 1,
			height: h || 1
		});
		for (const stack in stacks) for (const variant in stacks[stack]) {
			const glyphs = stacks[stack][variant];
			for (const id in glyphs) {
				const src = glyphs[id];
				if (!src || src.bitmap.width === 0 || src.bitmap.height === 0) continue;
				const bin = positions[stack][variant][id].rect;
				AlphaImage.copy(src.bitmap, image, {
					x: 0,
					y: 0
				}, {
					x: bin.x + padding,
					y: bin.y + padding
				}, src.bitmap);
			}
		}
		this.image = image;
		this.positions = positions;
	}
};
register("GlyphAtlas", GlyphAtlas);
//#endregion
//#region src/source/worker_tile.ts
var WorkerTile = class {
	constructor(params) {
		this.tileID = new OverscaledTileID(params.tileID.overscaledZ, params.tileID.wrap, params.tileID.canonical.z, params.tileID.canonical.x, params.tileID.canonical.y);
		this.uid = params.uid;
		this.zoom = params.zoom;
		this.pixelRatio = params.pixelRatio;
		this.tileSize = params.tileSize;
		this.source = params.source;
		this.overscaling = this.tileID.overscaleFactor();
		this.showCollisionBoxes = params.showCollisionBoxes;
		this.collectResourceTiming = !!params.collectResourceTiming;
		this.returnDependencies = !!params.returnDependencies;
		this.promoteId = params.promoteId;
		this.inFlightDependencies = [];
	}
	async parse(data, layerIndex, availableImages, actor, subdivisionGranularity) {
		this.data = data;
		this.collisionBoxArray = new CollisionBoxArray();
		const sourceLayerCoder = new DictionaryCoder(Object.keys(data.layers).sort());
		const featureIndex = new FeatureIndex(this.tileID, this.promoteId);
		featureIndex.bucketLayerIDs = [];
		const buckets = {};
		const options = {
			featureIndex,
			iconDependencies: {},
			patternDependencies: {},
			glyphDependencies: {},
			dashDependencies: {},
			availableImages,
			subdivisionGranularity
		};
		const layerFamilies = layerIndex.familiesBySource[this.source];
		for (const sourceLayerId in layerFamilies) {
			const sourceLayer = data.layers[sourceLayerId];
			if (!sourceLayer) continue;
			if (sourceLayer.version === 1) warnOnce(`Vector tile source "${this.source}" layer "${sourceLayerId}" does not use vector tile spec v2 and therefore may have some rendering errors.`);
			const sourceLayerIndex = sourceLayerCoder.encode(sourceLayerId);
			const features = [];
			for (let index = 0; index < sourceLayer.length; index++) {
				const feature = sourceLayer.feature(index);
				const id = featureIndex.getId(feature, sourceLayerId);
				features.push({
					feature,
					id,
					index,
					sourceLayerIndex
				});
			}
			for (const family of layerFamilies[sourceLayerId]) {
				const layer = family[0];
				if (layer.source !== this.source) warnOnce(`layer.source = ${layer.source} does not equal this.source = ${this.source}`);
				if (layer.isHidden(this.zoom, true)) continue;
				recalculateLayers(family, this.zoom, availableImages);
				(buckets[layer.id] = layer.createBucket({
					index: featureIndex.bucketLayerIDs.length,
					layers: family,
					zoom: this.zoom,
					pixelRatio: this.pixelRatio,
					overscaling: this.overscaling,
					collisionBoxArray: this.collisionBoxArray,
					sourceLayerIndex,
					sourceID: this.source
				})).populate(features, options, this.tileID.canonical);
				featureIndex.bucketLayerIDs.push(family.map((l) => l.id));
			}
		}
		const stacks = mapObject(options.glyphDependencies, (variants) => mapObject(variants, (glyphs) => Object.keys(glyphs)));
		for (const request of this.inFlightDependencies) request?.abort();
		this.inFlightDependencies = [];
		let getGlyphsPromise = Promise.resolve({});
		if (Object.keys(stacks).length) {
			const abortController = new AbortController();
			this.inFlightDependencies.push(abortController);
			getGlyphsPromise = actor.sendAsync({
				type: "GG",
				data: {
					stacks,
					source: this.source,
					tileID: this.tileID,
					type: "glyphs"
				}
			}, abortController);
		}
		const icons = Object.keys(options.iconDependencies);
		let getIconsPromise = Promise.resolve({});
		if (icons.length) {
			const abortController = new AbortController();
			this.inFlightDependencies.push(abortController);
			getIconsPromise = actor.sendAsync({
				type: "GI",
				data: {
					icons,
					source: this.source,
					tileID: this.tileID,
					type: "icons"
				}
			}, abortController);
		}
		const patterns = Object.keys(options.patternDependencies);
		let getPatternsPromise = Promise.resolve({});
		if (patterns.length) {
			const abortController = new AbortController();
			this.inFlightDependencies.push(abortController);
			getPatternsPromise = actor.sendAsync({
				type: "GI",
				data: {
					icons: patterns,
					source: this.source,
					tileID: this.tileID,
					type: "patterns"
				}
			}, abortController);
		}
		const dashes = options.dashDependencies;
		let getDashesPromise = Promise.resolve({});
		if (Object.keys(dashes).length) {
			const abortController = new AbortController();
			this.inFlightDependencies.push(abortController);
			getDashesPromise = actor.sendAsync({
				type: "GDA",
				data: { dashes }
			}, abortController);
		}
		const [glyphMap, iconMap, patternMap, dashPositions] = await Promise.all([
			getGlyphsPromise,
			getIconsPromise,
			getPatternsPromise,
			getDashesPromise
		]);
		const glyphAtlas = new GlyphAtlas(glyphMap);
		const imageAtlas = new ImageAtlas(iconMap, patternMap);
		for (const key in buckets) {
			const bucket = buckets[key];
			if (!bucket.hasDependencies) continue;
			recalculateLayers(bucket.layers, this.zoom, availableImages);
			bucket.addFeatures({
				options,
				canonical: this.tileID.canonical,
				glyphMap,
				glyphPositions: glyphAtlas.positions,
				iconMap,
				iconPositions: imageAtlas.iconPositions,
				patternMap,
				patternPositions: imageAtlas.patternPositions,
				dashPositions,
				showCollisionBoxes: this.showCollisionBoxes
			});
		}
		return {
			buckets: Object.values(buckets).filter((b) => !b.isEmpty()),
			featureIndex,
			collisionBoxArray: this.collisionBoxArray,
			glyphAtlasImage: glyphAtlas.image,
			imageAtlas,
			dashPositions,
			glyphMap: this.returnDependencies ? glyphMap : null,
			iconMap: this.returnDependencies ? iconMap : null,
			glyphPositions: this.returnDependencies ? glyphAtlas.positions : null
		};
	}
};
function recalculateLayers(layers, zoom, availableImages) {
	const parameters = new EvaluationParameters(zoom);
	for (const layer of layers) layer.recalculate(parameters, availableImages);
}
//#endregion
//#region src/source/worker_tile_state.ts
var WorkerTileState = class {
	constructor() {
		this.loading = {};
		this.loaded = {};
		this.parsing = {};
	}
	startLoading(uid, tile) {
		this.loading[uid] = tile;
	}
	finishLoading(uid) {
		delete this.loading[uid];
	}
	abort(uid) {
		const tile = this.loading[uid];
		if (!tile?.abort) return;
		tile.abort.abort();
		delete this.loading[uid];
	}
	getParsing(uid) {
		return this.parsing[uid];
	}
	setParsing(uid, state) {
		this.parsing[uid] = state;
	}
	removeParsing(uid) {
		delete this.parsing[uid];
	}
	markLoaded(uid, tile) {
		this.loaded[uid] = tile;
	}
	getLoaded(uid) {
		const tile = this.loaded[uid];
		if (!tile) return void 0;
		return tile;
	}
	removeLoaded(uid) {
		delete this.loaded[uid];
	}
	clearLoaded() {
		this.loaded = {};
	}
};
//#endregion
//#region src/util/request_performance.ts
/**
* @internal
* Safe wrapper for the performance resource timing API in web workers with graceful degradation
*/
var RequestPerformance = class {
	constructor(url) {
		this.start = `${url}#start`;
		this.end = `${url}#end`;
		this.measure = url;
		performance.mark(this.start);
	}
	finish() {
		performance.mark(this.end);
		let resourceTimingData = performance.getEntriesByName(this.measure);
		if (resourceTimingData.length === 0) {
			performance.measure(this.measure, this.start, this.end);
			resourceTimingData = performance.getEntriesByName(this.measure);
			performance.clearMarks(this.start);
			performance.clearMarks(this.end);
			performance.clearMeasures(this.measure);
		}
		return resourceTimingData;
	}
};
//#endregion
//#region src/source/vector_tile_overzoomed.ts
var VectorTileFeatureOverzoomed = class {
	constructor(type, geometry, properties, id, extent) {
		this.type = type;
		this.properties = properties ? properties : {};
		this.extent = extent;
		this.pointsArray = geometry;
		this.id = id;
	}
	loadGeometry() {
		return this.pointsArray.map((ring) => ring.map((point) => new Point(point.x, point.y)));
	}
};
var VectorTileLayerOverzoomed = class {
	constructor(features, layerName, extent) {
		this.version = 2;
		this._myFeatures = features;
		this.name = layerName;
		this.length = features.length;
		this.extent = extent;
	}
	feature(i) {
		return this._myFeatures[i];
	}
};
var VectorTileOverzoomed = class {
	constructor() {
		this.layers = {};
	}
	addLayer(layer) {
		this.layers[layer.name] = layer;
	}
};
/**
* This function slices a source tile layer into an overzoomed tile layer for a target tile ID.
* @param sourceLayer - the source tile layer to slice
* @param maxZoomTileID - the maximum zoom tile ID
* @param targetTileID - the target tile ID
* @returns - the overzoomed tile layer
*/
function sliceVectorTileLayer(sourceLayer, maxZoomTileID, targetTileID) {
	const { extent } = sourceLayer;
	const dz = targetTileID.z - maxZoomTileID.z;
	const scale = Math.pow(2, dz);
	const offsetX = (targetTileID.x - maxZoomTileID.x * scale) * extent;
	const offsetY = (targetTileID.y - maxZoomTileID.y * scale) * extent;
	const featureWrappers = [];
	for (let index = 0; index < sourceLayer.length; index++) {
		const feature = sourceLayer.feature(index);
		let geometry = feature.loadGeometry();
		for (const ring of geometry) for (const point of ring) {
			point.x = point.x * scale - offsetX;
			point.y = point.y * scale - offsetY;
		}
		const buffer = 128;
		geometry = clipGeometry(geometry, feature.type, -128, -128, extent + buffer, extent + buffer);
		if (geometry.length === 0) continue;
		featureWrappers.push(new VectorTileFeatureOverzoomed(feature.type, geometry, feature.properties, feature.id, extent));
	}
	return new VectorTileLayerOverzoomed(featureWrappers, sourceLayer.name, extent);
}
//#endregion
//#region src/source/vector_tile_worker_source.ts
/**
* The {@link WorkerSource} implementation that supports {@link VectorTileSource}. This class is
* used by vector tile sources to perform tile processing operations in a separate worker thread.
*/
var VectorTileWorkerSource = class {
	constructor(actor, layerIndex, availableImages) {
		this.actor = actor;
		this.layerIndex = layerIndex;
		this.availableImages = availableImages;
		this.tileState = new WorkerTileState();
		this.overzoomedTileResultCache = new BoundedLRUCache(1e3);
	}
	/**
	* Loads a vector tile
	*/
	loadVectorTile(params, rawData) {
		try {
			return {
				vectorTile: params.encoding !== "mlt" ? new VectorTile(new PbfReader(rawData)) : new MLTVectorTile(rawData),
				rawData
			};
		} catch (ex) {
			const bytes = new Uint8Array(rawData);
			const isGzipped = bytes[0] === 31 && bytes[1] === 139;
			let errorMessage = `Unable to parse the tile at ${params.request.url}, `;
			if (isGzipped) errorMessage += "please make sure the data is not gzipped and that you have configured the relevant header in the server";
			else errorMessage += `got error: ${ensureError(ex).message}`;
			throw new Error(errorMessage);
		}
	}
	/**
	* Implements {@link WorkerSource.loadTile}.
	*/
	async loadTile(params) {
		const { uid, overzoomParameters } = params;
		if (overzoomParameters) params.request = overzoomParameters.overzoomRequest;
		const timing = this._startRequestTiming(params);
		const workerTile = new WorkerTile(params);
		this.tileState.startLoading(uid, workerTile);
		const abortController = new AbortController();
		workerTile.abort = abortController;
		try {
			const tileResponse = await getArrayBuffer(params.request, abortController);
			if (params.etag && params.etag === tileResponse.etag) {
				this.tileState.finishLoading(uid);
				return this._getEtagUnmodifiedResult(tileResponse, timing);
			}
			const tileResult = this.loadVectorTile(params, tileResponse.data);
			this.tileState.finishLoading(uid);
			if (!tileResult) return null;
			let { vectorTile, rawData } = tileResult;
			if (overzoomParameters) ({vectorTile, rawData} = this._getOverzoomTile(params, vectorTile));
			const cacheControl = this._getExpiryData(tileResponse);
			const resourceTiming = this._finishRequestTiming(timing);
			workerTile.vectorTile = vectorTile;
			workerTile.etag = tileResponse.etag;
			this.tileState.markLoaded(uid, workerTile);
			const parsingState = {
				rawData,
				cacheControl,
				resourceTiming
			};
			this.tileState.setParsing(uid, parsingState);
			return await this._parseWorkerTile(workerTile, params);
		} catch (err) {
			this.tileState.finishLoading(uid);
			this.tileState.markLoaded(uid, workerTile);
			throw err;
		}
	}
	_getEtagUnmodifiedResult(response, timing) {
		const cacheControl = this._getExpiryData(response);
		const resourceTiming = this._finishRequestTiming(timing);
		return extend({ etagUnmodified: true }, cacheControl, resourceTiming);
	}
	async _parseWorkerTile(workerTile, params) {
		const parseState = this.tileState.getParsing(workerTile.uid);
		let result = await workerTile.parse(workerTile.vectorTile, this.layerIndex, this.availableImages, this.actor, params.subdivisionGranularity);
		if (parseState) {
			const { rawData, cacheControl, resourceTiming } = parseState;
			const encoding = params.overzoomParameters ? "mvt" : params.encoding;
			result = extend({
				rawTileData: rawData.slice(0),
				encoding
			}, result, cacheControl, resourceTiming);
			this.tileState.removeParsing(workerTile.uid);
		} else if (workerTile.etag) result = extend(result, { etag: workerTile.etag });
		return result;
	}
	_getExpiryData({ expires, cacheControl, etag }) {
		const data = {};
		if (expires) data.expires = expires;
		if (cacheControl) data.cacheControl = cacheControl;
		if (etag) data.etag = etag;
		return data;
	}
	_startRequestTiming(params) {
		if (!params.request?.collectResourceTiming) return;
		return new RequestPerformance(params.request.url);
	}
	_finishRequestTiming(timing) {
		const timingData = timing?.finish();
		if (!timingData) return {};
		return { resourceTiming: JSON.parse(JSON.stringify(timingData)) };
	}
	/**
	* If we are seeking a tile deeper than the source's max available canonical tile, get the overzoomed tile
	* @param params - the worker tile parameters
	* @param maxZoomVectorTile - the original vector tile at the source's max available canonical zoom
	* @returns the overzoomed tile and its raw data
	*/
	_getOverzoomTile(params, maxZoomVectorTile) {
		const { tileID, source, overzoomParameters } = params;
		const { maxZoomTileID } = overzoomParameters;
		const cacheKey = `${maxZoomTileID.key}_${tileID.key}_${params.request?.url}`;
		const cachedOverzoomTile = this.overzoomedTileResultCache.get(cacheKey);
		if (cachedOverzoomTile) return cachedOverzoomTile;
		const overzoomedVectorTile = new VectorTileOverzoomed();
		const layerFamilies = this.layerIndex.familiesBySource[source];
		for (const sourceLayerId in layerFamilies) {
			const sourceLayer = maxZoomVectorTile.layers[sourceLayerId];
			if (!sourceLayer) continue;
			const slicedTileLayer = sliceVectorTileLayer(sourceLayer, maxZoomTileID, tileID.canonical);
			if (slicedTileLayer.length > 0) overzoomedVectorTile.addLayer(slicedTileLayer);
		}
		const overzoomedVectorTileResult = {
			vectorTile: overzoomedVectorTile,
			rawData: fromVectorTileJs(overzoomedVectorTile).buffer
		};
		this.overzoomedTileResultCache.set(cacheKey, overzoomedVectorTileResult);
		return overzoomedVectorTileResult;
	}
	/**
	* Implements {@link WorkerSource.reloadTile}.
	*/
	async reloadTile(params) {
		const uid = params.uid;
		const workerTile = this.tileState.getLoaded(uid);
		if (!workerTile) throw new Error("Should not be trying to reload a tile that was never loaded or has been removed");
		if (!workerTile.vectorTile) return;
		workerTile.showCollisionBoxes = params.showCollisionBoxes;
		return await this._parseWorkerTile(workerTile, params);
	}
	/**
	* Implements {@link WorkerSource.abortTile}.
	*/
	async abortTile(params) {
		this.tileState.abort(params.uid);
	}
	/**
	* Implements {@link WorkerSource.removeTile}.
	*/
	async removeTile(params) {
		this.tileState.removeLoaded(params.uid);
	}
};
//#endregion
//#region src/source/raster_dem_tile_worker_source.ts
var RasterDEMTileWorkerSource = class {
	constructor() {
		this.loaded = {};
	}
	async loadTile(params) {
		const { uid, encoding, rawImageData, redFactor, greenFactor, blueFactor, baseShift } = params;
		const width = rawImageData.width + 4;
		const height = rawImageData.height + 4;
		const imagePixels = isImageBitmap(rawImageData) ? new RGBAImage({
			width,
			height
		}, await getImageData(rawImageData, -2, -2, width, height)) : rawImageData;
		const dem = new DEMData(uid, imagePixels, encoding, redFactor, greenFactor, blueFactor, baseShift);
		this.loaded ||= {};
		this.loaded[uid] = dem;
		return dem;
	}
	removeTile(params) {
		const loaded = this.loaded, uid = params.uid;
		if (loaded?.[uid]) delete loaded[uid];
	}
};
//#endregion
//#region src/source/geojson_worker_source.ts
/**
* The {@link WorkerSource} implementation that supports {@link GeoJSONSource}.
* This class is designed to be easily reused to support custom source types
* for data formats that can be parsed/converted into an in-memory GeoJSON
* representation. To do so, create it with
* `new GeoJSONWorkerSource(actor, layerIndex, customLoadGeoJSONFunction)`.
* For a full example, see [mapbox-gl-topojson](https://github.com/developmentseed/mapbox-gl-topojson).
*/
var GeoJSONWorkerSource = class {
	constructor(actor, layerIndex, availableImages, createGeoJSONIndexFunc = createGeoJSONIndex) {
		this.actor = actor;
		this.layerIndex = layerIndex;
		this.availableImages = availableImages;
		this.tileState = new WorkerTileState();
		this._createGeoJSONIndex = createGeoJSONIndexFunc;
	}
	/**
	* Retrieves and sends loaded vector tiles to the main thread.
	*/
	loadVectorTile(params) {
		if (!this._geoJSONIndex) throw new Error("Unable to parse the data into a cluster or geojson");
		const { z, x, y } = params.tileID.canonical;
		const geoJSONTile = this._geoJSONIndex.getTile(z, x, y);
		if (!geoJSONTile) return null;
		const geojsonWrapper = new GeoJSONWrapper(geoJSONTile.features, {
			version: 2,
			extent: EXTENT
		});
		return {
			vectorTile: geojsonWrapper,
			rawData: fromVectorTileJs(geojsonWrapper, JSON_PREFIX).buffer
		};
	}
	/**
	* Implements {@link WorkerSource.loadTile}.
	*/
	async loadTile(params) {
		const { uid } = params;
		const workerTile = new WorkerTile(params);
		workerTile.abort = new AbortController();
		try {
			const loadResult = this.loadVectorTile(params);
			if (!loadResult) return null;
			const { vectorTile, rawData } = loadResult;
			workerTile.vectorTile = vectorTile;
			this.tileState.markLoaded(uid, workerTile);
			const parsingState = { rawData };
			this.tileState.setParsing(uid, parsingState);
			return await this._parseWorkerTile(workerTile, params);
		} catch (err) {
			this.tileState.markLoaded(uid, workerTile);
			throw err;
		}
	}
	async _parseWorkerTile(workerTile, params) {
		const parseState = this.tileState.getParsing(workerTile.uid);
		let result = await workerTile.parse(workerTile.vectorTile, this.layerIndex, this.availableImages, this.actor, params.subdivisionGranularity);
		if (parseState) {
			const { rawData } = parseState;
			result = extend({
				rawTileData: rawData.slice(0),
				encoding: "mvt"
			}, result);
			this.tileState.removeParsing(workerTile.uid);
		}
		return result;
	}
	/**
	* Implements {@link WorkerSource.abortTile}.
	*/
	async abortTile(params) {
		this.tileState.abort(params.uid);
	}
	/**
	* Implements {@link WorkerSource.removeTile}.
	*/
	async removeTile(params) {
		this.tileState.removeLoaded(params.uid);
	}
	/**
	* Fetches (if appropriate), parses and indexes geojson data into tiles. This
	* preparatory method must be called before {@link GeoJSONWorkerSource.loadTile}
	* can correctly serve up tiles. The first call to this method must contain a valid
	* {@link params.data}, {@link params.request} or {@link params.dataDiff}. Subsequent
	* calls may omit these parameters to reprocess the existing data (such as to update
	* clustering options).
	*
	* Defers to {@link GeoJSONWorkerSource.loadAndProcessGeoJSON} for the pre-processing.
	*
	* When a `loadData` request comes in while a previous one is being processed,
	* the previous one is aborted.
	*
	* @param params - the parameters
	* @returns a promise that resolves when the data is loaded and parsed into a GeoJSON object
	*/
	async loadData(params) {
		this._pendingRequest?.abort();
		const timing = this._startRequestTiming(params);
		this._pendingRequest = new AbortController();
		try {
			await this.loadAndProcessGeoJSON(params, this._pendingRequest);
			delete this._pendingRequest;
			this.tileState.clearLoaded();
			const result = {};
			if (params.request) result.data = params.data;
			this._finishRequestTiming(timing, params, result);
			return result;
		} catch (err) {
			delete this._pendingRequest;
			if (!isAbortError(err)) throw err;
			return { abandoned: true };
		}
	}
	_startRequestTiming(params) {
		if (!params.request?.collectResourceTiming) return;
		return new RequestPerformance(params.request.url);
	}
	_finishRequestTiming(timing, params, result) {
		const timingData = timing?.finish();
		if (!timingData) return;
		result.resourceTiming = { [params.source]: JSON.parse(JSON.stringify(timingData)) };
	}
	/**
	* Implements {@link WorkerSource.reloadTile}.
	*
	* If the tile is loaded, reload by re-parsing the already available tile data.
	* Otherwise, such as after a setData() call, we load the tile fresh.
	*
	* @param params - the parameters
	* @returns A promise that resolves when the tile is reloaded
	*/
	async reloadTile(params) {
		const uid = params.uid;
		const workerTile = this.tileState.getLoaded(uid);
		if (!workerTile) return await this.loadTile(params);
		if (!workerTile.vectorTile) return;
		workerTile.showCollisionBoxes = params.showCollisionBoxes;
		return await this._parseWorkerTile(workerTile, params);
	}
	/**
	* Fetch, parse and process GeoJSON according to the given parameters.
	* Defers to {@link GeoJSONWorkerSource._loadGeoJSONFromString} for the fetching and parsing.
	*
	* @param params - the parameters
	* @param abortController - the abort controller that allows aborting this operation
	* @returns a promise that is resolved with the processes GeoJSON
	*/
	async loadAndProcessGeoJSON(params, abortController) {
		if (params.request) params.data = (await getJSON(params.request, abortController)).data;
		if (params.data) {
			params.data = this._filterGeoJSON(params.data, params.filter, params.source);
			this._geoJSONIndex = this._createGeoJSONIndex(params.data, params);
			return;
		}
		if (params.dataDiff) {
			this._geoJSONIndex ??= this._createGeoJSONIndex({
				type: "FeatureCollection",
				features: []
			}, params);
			this._geoJSONIndex.updateData(params.dataDiff, this._getFilterPredicate(params.filter, params.source));
			return;
		}
		if (params.updateCluster) this._geoJSONIndex.updateClusterOptions(params.geojsonVtOptions.cluster, getSuperclusterOptions(params));
		if (this._geoJSONIndex == null) throw new Error(`Input data given to '${params.source}' is not a valid GeoJSON object.`);
	}
	/**
	* Applies a filter to a GeoJSON object.
	*/
	_filterGeoJSON(data, filter, source) {
		if (data.type !== "FeatureCollection") return data;
		const predicate = this._getFilterPredicate(filter, source);
		if (!predicate) return data;
		return {
			type: "FeatureCollection",
			features: data.features.filter((feature) => predicate(feature))
		};
	}
	/**
	* Gets a predicate function that can be used to filter GeoJSON features.
	*/
	_getFilterPredicate(filter, source) {
		if (typeof filter !== "boolean" && !filter?.length) return void 0;
		const compiled = createExpression(filter, `sources.${source}.filter`, {
			type: "boolean",
			"property-type": "data-driven",
			overridable: false,
			transition: false
		});
		if (compiled.result === "error") throw new Error(compiled.value.map((err) => `${err.key}: ${err.message}`).join(", "));
		return (feature) => compiled.value.evaluate({ zoom: 0 }, feature);
	}
	async removeSource(_params) {
		this._pendingRequest?.abort();
	}
	getClusterExpansionZoom(params) {
		return this._geoJSONIndex.getClusterExpansionZoom(params.clusterId);
	}
	getClusterChildren(params) {
		return this._geoJSONIndex.getClusterChildren(params.clusterId);
	}
	getClusterLeaves(params) {
		return this._geoJSONIndex.getClusterLeaves(params.clusterId, params.limit, params.offset);
	}
};
function createGeoJSONIndex(data, params) {
	const options = extend(params.geojsonVtOptions || {}, {
		updateable: true,
		clusterOptions: getSuperclusterOptions(params)
	});
	return new GeoJSONVT(data, options);
}
function getSuperclusterOptions({ geojsonVtOptions, clusterProperties, source }) {
	if (!clusterProperties || !geojsonVtOptions.clusterOptions) return geojsonVtOptions.clusterOptions;
	const mapExpressions = {};
	const reduceExpressions = {};
	const globals = {
		accumulated: null,
		zoom: 0
	};
	const feature = { properties: null };
	const propertyNames = Object.keys(clusterProperties);
	for (const key of propertyNames) {
		const [operator, mapExpression] = clusterProperties[key];
		const mapExpressionParsed = createExpression(mapExpression, `sources.${source}.clusterProperties.${key}[1]`);
		const reduceExpressionParsed = createExpression(typeof operator === "string" ? [
			operator,
			["accumulated"],
			["get", key]
		] : operator, `sources.${source}.clusterProperties.${key}[0]`);
		mapExpressions[key] = mapExpressionParsed.value;
		reduceExpressions[key] = reduceExpressionParsed.value;
	}
	geojsonVtOptions.clusterOptions.map = (pointProperties) => {
		feature.properties = pointProperties;
		const properties = {};
		for (const key of propertyNames) properties[key] = mapExpressions[key].evaluate(globals, feature);
		return properties;
	};
	geojsonVtOptions.clusterOptions.reduce = (accumulated, clusterProperties) => {
		feature.properties = clusterProperties;
		for (const key of propertyNames) {
			globals.accumulated = accumulated[key];
			accumulated[key] = reduceExpressions[key].evaluate(globals, feature);
		}
	};
	return geojsonVtOptions.clusterOptions;
}
//#endregion
//#region src/source/worker.ts
/**
* Loads an external script into worker (global) scope. The loader picks a
* strategy based on what the script actually is:
*
* - `.mjs` URLs: dynamic `import()` directly, no fetch/sniff overhead. Worker
*   CSP needs `script-src` to permit the URL.
*
* - Other URLs: fetch the source and sniff for ESM syntax (top-level `import`
*   or `export`). If ESM is detected, run it through a blob-URL dynamic
*   `import()` so the browser parses it as a module; this requires
*   `script-src blob:` in the worker CSP. Otherwise treat it as UMD/IIFE and
*   run it via `globalThis.eval`, which requires `script-src 'unsafe-eval'`.
*/
async function loadScript(url) {
	if (url.endsWith(".mjs")) {
		await import(
			/* @vite-ignore */
			url
);
		return;
	}
	const response = await fetch(url, { credentials: "same-origin" });
	if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
	const code = await response.text();
	if (/^[ \t]*(import|export)\s/m.test(code)) {
		const blobUrl = URL.createObjectURL(new Blob([code], { type: "text/javascript" }));
		try {
			await import(
				/* @vite-ignore */
				blobUrl
);
		} finally {
			URL.revokeObjectURL(blobUrl);
		}
		return;
	}
	globalThis.eval(code);
}
/**
* The Worker class responsible for background thread related execution
*/
var Worker = class {
	constructor(self) {
		this.self = self;
		this.actor = new Actor(self);
		this.layerIndexes = {};
		this.availableImages = {};
		this.workerSources = {};
		this.demWorkerSources = {};
		this.externalWorkerSourceTypes = {};
		this.globalStates = /* @__PURE__ */ new Map();
		this.self.registerWorkerSource = (name, WorkerSource) => {
			if (this.externalWorkerSourceTypes[name]) throw new Error(`Worker source with name "${name}" already registered.`);
			this.externalWorkerSourceTypes[name] = WorkerSource;
		};
		this.self.addProtocol = addProtocol;
		this.self.removeProtocol = removeProtocol;
		/**
		* Invoked by a right-to-left text plugin once it has fetched and parsed.
		*
		* @deprecated MapLibre shapes Arabic and reorders bidirectional text itself. A plugin
		* registered here still replaces the built-in implementation, but this will be removed in a
		* future release.
		*/
		this.self.registerRTLTextPlugin = (rtlTextPlugin) => {
			rtlWorkerPlugin.setMethods(rtlTextPlugin);
		};
		this.self.makeRequest = makeRequest;
		this.actor.registerMessageHandler("LDT", (mapId, params) => {
			return this._getDEMWorkerSource(mapId, params.source).loadTile(params);
		});
		this.actor.registerMessageHandler("RDT", async (mapId, params) => {
			this._getDEMWorkerSource(mapId, params.source).removeTile(params);
		});
		this.actor.registerMessageHandler("GCEZ", async (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).getClusterExpansionZoom(params);
		});
		this.actor.registerMessageHandler("GCC", async (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).getClusterChildren(params);
		});
		this.actor.registerMessageHandler("GCL", async (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).getClusterLeaves(params);
		});
		this.actor.registerMessageHandler("LD", (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).loadData(params);
		});
		this.actor.registerMessageHandler("LT", (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).loadTile(params);
		});
		this.actor.registerMessageHandler("RT", (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).reloadTile(params);
		});
		this.actor.registerMessageHandler("AT", (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).abortTile(params);
		});
		this.actor.registerMessageHandler("RMT", (mapId, params) => {
			return this._getWorkerSource(mapId, params.type, params.source).removeTile(params);
		});
		this.actor.registerMessageHandler("RS", async (mapId, params) => {
			if (!this.workerSources[mapId]?.[params.type]?.[params.source]) return;
			const worker = this.workerSources[mapId][params.type][params.source];
			delete this.workerSources[mapId][params.type][params.source];
			if (worker.removeSource !== void 0) worker.removeSource(params);
		});
		this.actor.registerMessageHandler("RM", async (mapId) => {
			delete this.layerIndexes[mapId];
			delete this.availableImages[mapId];
			delete this.workerSources[mapId];
			delete this.demWorkerSources[mapId];
			this.globalStates.delete(mapId);
		});
		this.actor.registerMessageHandler("SR", async (_mapId, params) => {
			this.referrer = params;
		});
		this.actor.registerMessageHandler("SRPS", (mapId, params) => {
			return this._syncRTLPluginState(mapId, params);
		});
		this.actor.registerMessageHandler("IS", async (_mapId, params) => {
			await loadScript(params);
		});
		this.actor.registerMessageHandler("SI", (mapId, params) => {
			return this._setImages(mapId, params);
		});
		this.actor.registerMessageHandler("UL", async (mapId, params) => {
			this._getLayerIndex(mapId).update(params.layers, params.removedIds, this._getGlobalState(mapId));
		});
		this.actor.registerMessageHandler("UGS", async (mapId, params) => {
			const globalState = this._getGlobalState(mapId);
			for (const key in params) globalState[key] = params[key];
		});
		this.actor.registerMessageHandler("SL", async (mapId, params) => {
			this._getLayerIndex(mapId).replace(params, this._getGlobalState(mapId));
		});
	}
	_getGlobalState(mapId) {
		let state = this.globalStates.get(mapId);
		if (!state) {
			state = {};
			this.globalStates.set(mapId, state);
		}
		return state;
	}
	async _setImages(mapId, images) {
		this.availableImages[mapId] = images;
		for (const workerSource in this.workerSources[mapId]) {
			const ws = this.workerSources[mapId][workerSource];
			for (const source in ws) ws[source].availableImages = images;
		}
	}
	async _syncRTLPluginState(mapId, incomingState) {
		return await rtlWorkerPlugin.syncState(incomingState, loadScript);
	}
	_getAvailableImages(mapId) {
		let availableImages = this.availableImages[mapId];
		availableImages ||= [];
		return availableImages;
	}
	_getLayerIndex(mapId) {
		let layerIndexes = this.layerIndexes[mapId];
		layerIndexes ||= this.layerIndexes[mapId] = new StyleLayerIndex();
		return layerIndexes;
	}
	/**
	* This is basically a lazy initialization of a worker per mapId and sourceType and sourceName
	* @param mapId - the mapId
	* @param sourceType - the source type - 'vector' for example
	* @param sourceName - the source name - 'osm' for example
	* @returns a new instance or a cached one
	*/
	_getWorkerSource(mapId, sourceType, sourceName) {
		this.workerSources[mapId] ||= {};
		this.workerSources[mapId][sourceType] ||= {};
		if (!this.workerSources[mapId][sourceType][sourceName]) {
			const actor = { sendAsync: (message, abortController) => {
				message.targetMapId = mapId;
				return this.actor.sendAsync(message, abortController);
			} };
			switch (sourceType) {
				case "vector":
					this.workerSources[mapId][sourceType][sourceName] = new VectorTileWorkerSource(actor, this._getLayerIndex(mapId), this._getAvailableImages(mapId));
					break;
				case "geojson":
					this.workerSources[mapId][sourceType][sourceName] = new GeoJSONWorkerSource(actor, this._getLayerIndex(mapId), this._getAvailableImages(mapId));
					break;
				default: this.workerSources[mapId][sourceType][sourceName] = new this.externalWorkerSourceTypes[sourceType](actor, this._getLayerIndex(mapId), this._getAvailableImages(mapId));
			}
		}
		return this.workerSources[mapId][sourceType][sourceName];
	}
	/**
	* This is basically a lazy initialization of a worker per mapId and source
	* @param mapId - the mapId
	* @param sourceType - the source type - 'raster-dem' for example
	* @returns a new instance or a cached one
	*/
	_getDEMWorkerSource(mapId, sourceType) {
		this.demWorkerSources[mapId] ||= {};
		this.demWorkerSources[mapId][sourceType] ||= new RasterDEMTileWorkerSource();
		return this.demWorkerSources[mapId][sourceType];
	}
};
if (isWorker(self)) self.worker = new Worker(self);
//#endregion
export { Worker as default };

//# sourceMappingURL=maplibre-gl-worker-dev.mjs.map