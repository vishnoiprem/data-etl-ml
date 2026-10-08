import { deepEqual } from "./util/deep_equal.mjs";
//#region src/diff.ts
/**
* The main reason for this method is to allow type check when adding a command to the array.
* @param commands - The commands array to add to
* @param command - The command to add
*/
function addCommand(commands, command) {
	commands.push(command);
}
function addSource(sourceId, after, commands) {
	addCommand(commands, {
		command: "addSource",
		args: [sourceId, after[sourceId]]
	});
}
function removeSource(sourceId, commands, sourcesRemoved) {
	addCommand(commands, {
		command: "removeSource",
		args: [sourceId]
	});
	sourcesRemoved[sourceId] = true;
}
function updateSource(sourceId, after, commands, sourcesRemoved) {
	removeSource(sourceId, commands, sourcesRemoved);
	addSource(sourceId, after, commands);
}
function canUpdateGeoJSON(before, after, sourceId) {
	let prop;
	for (prop in before[sourceId]) {
		if (!Object.prototype.hasOwnProperty.call(before[sourceId], prop)) continue;
		if (prop !== "data" && !deepEqual(before[sourceId][prop], after[sourceId][prop])) return false;
	}
	for (prop in after[sourceId]) {
		if (!Object.prototype.hasOwnProperty.call(after[sourceId], prop)) continue;
		if (prop !== "data" && !deepEqual(before[sourceId][prop], after[sourceId][prop])) return false;
	}
	return true;
}
function diffSources(before, after, commands, sourcesRemoved) {
	before = before || {};
	after = after || {};
	let sourceId;
	for (sourceId in before) {
		if (!Object.prototype.hasOwnProperty.call(before, sourceId)) continue;
		if (!Object.prototype.hasOwnProperty.call(after, sourceId)) removeSource(sourceId, commands, sourcesRemoved);
	}
	for (sourceId in after) {
		if (!Object.prototype.hasOwnProperty.call(after, sourceId)) continue;
		if (!Object.prototype.hasOwnProperty.call(before, sourceId)) addSource(sourceId, after, commands);
		else if (!deepEqual(before[sourceId], after[sourceId])) {
			if (before[sourceId].type === "geojson" && after[sourceId].type === "geojson" && canUpdateGeoJSON(before, after, sourceId)) addCommand(commands, {
				command: "setGeoJSONSourceData",
				args: [sourceId, after[sourceId].data]
			});
			else updateSource(sourceId, after, commands, sourcesRemoved);
		}
	}
}
/**
* Adds a paint or layout property command for a single property of a layer.
* The property names are taken from a layer's paint/layout object, so they are known to be
* valid names for the given command, which a `for ... in` loop over that object can't express.
* @param after - The paint or layout object to take the property value from
* @param commands - The commands array to add to
* @param layerId - The id of the layer the property belongs to
* @param prop - The name of the property that changed
* @param command - The command to add
*/
function addPropertyCommand(after, commands, layerId, prop, command) {
	if (command === "setPaintProperty") addCommand(commands, {
		command,
		args: [
			layerId,
			prop,
			after[prop]
		]
	});
	else addCommand(commands, {
		command,
		args: [
			layerId,
			prop,
			after[prop]
		]
	});
}
function diffLayerPropertyChanges(before, after, commands, layerId, command) {
	before = before || {};
	after = after || {};
	for (const prop in before) {
		if (!Object.prototype.hasOwnProperty.call(before, prop)) continue;
		if (!deepEqual(before[prop], after[prop])) addPropertyCommand(after, commands, layerId, prop, command);
	}
	for (const prop in after) {
		if (!Object.prototype.hasOwnProperty.call(after, prop) || Object.prototype.hasOwnProperty.call(before, prop)) continue;
		if (!deepEqual(before[prop], after[prop])) addPropertyCommand(after, commands, layerId, prop, command);
	}
}
function pluckId(layer) {
	return layer.id;
}
function indexById(group, layer) {
	group[layer.id] = layer;
	return group;
}
function diffLayers(before, after, commands) {
	before = before || [];
	after = after || [];
	const beforeOrder = before.map(pluckId);
	const afterOrder = after.map(pluckId);
	const beforeIndex = before.reduce(indexById, {});
	const afterIndex = after.reduce(indexById, {});
	const tracker = beforeOrder.slice();
	const clean = Object.create(null);
	let layerId;
	let beforeLayer;
	let afterLayer;
	let insertBeforeLayerId;
	let prop;
	for (let i = 0, d = 0; i < beforeOrder.length; i++) {
		layerId = beforeOrder[i];
		if (!Object.prototype.hasOwnProperty.call(afterIndex, layerId)) {
			addCommand(commands, {
				command: "removeLayer",
				args: [layerId]
			});
			tracker.splice(tracker.indexOf(layerId, d), 1);
		} else d++;
	}
	for (let i = 0, d = 0; i < afterOrder.length; i++) {
		layerId = afterOrder[afterOrder.length - 1 - i];
		if (tracker[tracker.length - 1 - i] === layerId) continue;
		if (Object.prototype.hasOwnProperty.call(beforeIndex, layerId)) {
			addCommand(commands, {
				command: "removeLayer",
				args: [layerId]
			});
			tracker.splice(tracker.lastIndexOf(layerId, tracker.length - d), 1);
		} else d++;
		insertBeforeLayerId = tracker[tracker.length - i];
		addCommand(commands, {
			command: "addLayer",
			args: [afterIndex[layerId], insertBeforeLayerId]
		});
		tracker.splice(tracker.length - i, 0, layerId);
		clean[layerId] = true;
	}
	for (let i = 0; i < afterOrder.length; i++) {
		layerId = afterOrder[i];
		beforeLayer = beforeIndex[layerId];
		afterLayer = afterIndex[layerId];
		if (clean[layerId] || deepEqual(beforeLayer, afterLayer)) continue;
		if (!deepEqual(beforeLayer.source, afterLayer.source) || !deepEqual(beforeLayer["source-layer"], afterLayer["source-layer"]) || !deepEqual(beforeLayer.type, afterLayer.type)) {
			addCommand(commands, {
				command: "removeLayer",
				args: [layerId]
			});
			insertBeforeLayerId = tracker[tracker.lastIndexOf(layerId) + 1];
			addCommand(commands, {
				command: "addLayer",
				args: [afterLayer, insertBeforeLayerId]
			});
			continue;
		}
		diffLayerPropertyChanges(beforeLayer.layout, afterLayer.layout, commands, layerId, "setLayoutProperty");
		diffLayerPropertyChanges(beforeLayer.paint, afterLayer.paint, commands, layerId, "setPaintProperty");
		if (!deepEqual(beforeLayer.filter, afterLayer.filter)) addCommand(commands, {
			command: "setFilter",
			args: [layerId, afterLayer.filter]
		});
		if (!deepEqual(beforeLayer.minzoom, afterLayer.minzoom) || !deepEqual(beforeLayer.maxzoom, afterLayer.maxzoom)) addCommand(commands, {
			command: "setLayerZoomRange",
			args: [
				layerId,
				afterLayer.minzoom,
				afterLayer.maxzoom
			]
		});
		for (prop in beforeLayer) {
			if (!Object.prototype.hasOwnProperty.call(beforeLayer, prop)) continue;
			if (prop === "layout" || prop === "paint" || prop === "filter" || prop === "metadata" || prop === "minzoom" || prop === "maxzoom") continue;
			if (prop.indexOf("paint.") === 0) diffLayerPropertyChanges(beforeLayer[prop], afterLayer[prop], commands, layerId, "setPaintProperty");
			else if (!deepEqual(beforeLayer[prop], afterLayer[prop])) addCommand(commands, {
				command: "setLayerProperty",
				args: [
					layerId,
					prop,
					afterLayer[prop]
				]
			});
		}
		for (prop in afterLayer) {
			if (!Object.prototype.hasOwnProperty.call(afterLayer, prop) || Object.prototype.hasOwnProperty.call(beforeLayer, prop)) continue;
			if (prop === "layout" || prop === "paint" || prop === "filter" || prop === "metadata" || prop === "minzoom" || prop === "maxzoom") continue;
			if (prop.indexOf("paint.") === 0) diffLayerPropertyChanges(beforeLayer[prop], afterLayer[prop], commands, layerId, "setPaintProperty");
			else if (!deepEqual(beforeLayer[prop], afterLayer[prop])) addCommand(commands, {
				command: "setLayerProperty",
				args: [
					layerId,
					prop,
					afterLayer[prop]
				]
			});
		}
	}
}
/**
* Diff two stylesheet
*
* Creates semanticly aware diffs that can easily be applied at runtime.
* Operations produced by the diff closely resemble the maplibre-gl-js API. Any
* error creating the diff will fall back to the 'setStyle' operation.
*
* Example diff:
* [
*     { command: 'setConstant', args: ['@water', '#0000FF'] },
*     { command: 'setPaintProperty', args: ['background', 'background-color', 'black'] }
* ]
*
* @private
* @param {*} [before] stylesheet to compare from
* @param {*} after stylesheet to compare to
* @returns Array list of changes
*/
function diff(before, after) {
	if (!before) return [{
		command: "setStyle",
		args: [after]
	}];
	let commands = [];
	try {
		if (!deepEqual(before.version, after.version)) return [{
			command: "setStyle",
			args: [after]
		}];
		if (!deepEqual(before.center, after.center)) commands.push({
			command: "setCenter",
			args: [after.center]
		});
		if (!deepEqual(before.state, after.state)) commands.push({
			command: "setGlobalState",
			args: [after.state]
		});
		if (!deepEqual(before.centerAltitude, after.centerAltitude)) commands.push({
			command: "setCenterAltitude",
			args: [after.centerAltitude]
		});
		if (!deepEqual(before.zoom, after.zoom)) commands.push({
			command: "setZoom",
			args: [after.zoom]
		});
		if (!deepEqual(before.bearing, after.bearing)) commands.push({
			command: "setBearing",
			args: [after.bearing]
		});
		if (!deepEqual(before.pitch, after.pitch)) commands.push({
			command: "setPitch",
			args: [after.pitch]
		});
		if (!deepEqual(before.roll, after.roll)) commands.push({
			command: "setRoll",
			args: [after.roll]
		});
		if (!deepEqual(before.sprite, after.sprite)) commands.push({
			command: "setSprite",
			args: [after.sprite]
		});
		if (!deepEqual(before.glyphs, after.glyphs)) commands.push({
			command: "setGlyphs",
			args: [after.glyphs]
		});
		if (!deepEqual(before["font-faces"], after["font-faces"])) commands.push({
			command: "setFontFaces",
			args: [after["font-faces"]]
		});
		if (!deepEqual(before.transition, after.transition)) commands.push({
			command: "setTransition",
			args: [after.transition]
		});
		if (!deepEqual(before.light, after.light)) commands.push({
			command: "setLight",
			args: [after.light]
		});
		const terrainChanged = !deepEqual(before.terrain, after.terrain);
		if (terrainChanged && !after.terrain) commands.push({
			command: "setTerrain",
			args: [void 0]
		});
		if (!deepEqual(before.sky, after.sky)) commands.push({
			command: "setSky",
			args: [after.sky]
		});
		if (!deepEqual(before.projection, after.projection)) commands.push({
			command: "setProjection",
			args: [after.projection]
		});
		const sourcesRemoved = {};
		const removeOrAddSourceCommands = [];
		diffSources(before.sources, after.sources, removeOrAddSourceCommands, sourcesRemoved);
		const beforeLayers = [];
		if (before.layers) before.layers.forEach((layer) => {
			if ("source" in layer && sourcesRemoved[layer.source]) commands.push({
				command: "removeLayer",
				args: [layer.id]
			});
			else beforeLayers.push(layer);
		});
		commands = commands.concat(removeOrAddSourceCommands);
		diffLayers(beforeLayers, after.layers, commands);
		if (terrainChanged && after.terrain) commands.push({
			command: "setTerrain",
			args: [after.terrain]
		});
	} catch (e) {
		console.warn("Unable to compute style diff:", e);
		commands = [{
			command: "setStyle",
			args: [after]
		}];
	}
	return commands;
}
//#endregion
export { diff };

//# sourceMappingURL=diff.mjs.map