import { BooleanType } from "../types.mjs";
import { isValue } from "../values.mjs";
import { EXTENT, boxWithinBox, getTileCoordinates, lineStringWithinPolygon, lineStringWithinPolygons, pointWithinPolygon, pointWithinPolygons, updateBBox } from "../../util/geometry_util.mjs";
//#region src/expression/definitions/within.ts
function getTilePolygon(coordinates, bbox, canonical) {
	const polygon = [];
	for (let i = 0; i < coordinates.length; i++) {
		const ring = [];
		for (let j = 0; j < coordinates[i].length; j++) {
			const coord = getTileCoordinates(coordinates[i][j], canonical);
			updateBBox(bbox, coord);
			ring.push(coord);
		}
		polygon.push(ring);
	}
	return polygon;
}
function getTilePolygons(coordinates, bbox, canonical) {
	const polygons = [];
	for (let i = 0; i < coordinates.length; i++) {
		const polygon = getTilePolygon(coordinates[i], bbox, canonical);
		polygons.push(polygon);
	}
	return polygons;
}
function updatePoint(p, bbox, polyBBox, worldSize) {
	if (p[0] < polyBBox[0] || p[0] > polyBBox[2]) {
		const halfWorldSize = worldSize * .5;
		let shift = p[0] - polyBBox[0] > halfWorldSize ? -worldSize : polyBBox[0] - p[0] > halfWorldSize ? worldSize : 0;
		if (shift === 0) shift = p[0] - polyBBox[2] > halfWorldSize ? -worldSize : polyBBox[2] - p[0] > halfWorldSize ? worldSize : 0;
		p[0] += shift;
	}
	updateBBox(bbox, p);
}
function resetBBox(bbox) {
	bbox[0] = bbox[1] = Infinity;
	bbox[2] = bbox[3] = -Infinity;
}
function getTilePoints(geometry, pointBBox, polyBBox, canonical) {
	const worldSize = Math.pow(2, canonical.z) * EXTENT;
	const shifts = [canonical.x * EXTENT, canonical.y * EXTENT];
	const tilePoints = [];
	for (const points of geometry) for (const point of points) {
		const p = [point.x + shifts[0], point.y + shifts[1]];
		updatePoint(p, pointBBox, polyBBox, worldSize);
		tilePoints.push(p);
	}
	return tilePoints;
}
function getTileLines(geometry, lineBBox, polyBBox, canonical) {
	const worldSize = Math.pow(2, canonical.z) * EXTENT;
	const shifts = [canonical.x * EXTENT, canonical.y * EXTENT];
	const tileLines = [];
	for (const line of geometry) {
		const tileLine = [];
		for (const point of line) {
			const p = [point.x + shifts[0], point.y + shifts[1]];
			updateBBox(lineBBox, p);
			tileLine.push(p);
		}
		tileLines.push(tileLine);
	}
	if (lineBBox[2] - lineBBox[0] <= worldSize / 2) {
		resetBBox(lineBBox);
		for (const line of tileLines) for (const p of line) updatePoint(p, lineBBox, polyBBox, worldSize);
	}
	return tileLines;
}
function pointsWithinPolygons(ctx, polygonGeometry) {
	const pointBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const polyBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const canonical = ctx.canonicalID();
	if (polygonGeometry.type === "Polygon") {
		const tilePolygon = getTilePolygon(polygonGeometry.coordinates, polyBBox, canonical);
		const tilePoints = getTilePoints(ctx.geometry(), pointBBox, polyBBox, canonical);
		if (!boxWithinBox(pointBBox, polyBBox)) return false;
		for (const point of tilePoints) if (!pointWithinPolygon(point, tilePolygon)) return false;
	}
	if (polygonGeometry.type === "MultiPolygon") {
		const tilePolygons = getTilePolygons(polygonGeometry.coordinates, polyBBox, canonical);
		const tilePoints = getTilePoints(ctx.geometry(), pointBBox, polyBBox, canonical);
		if (!boxWithinBox(pointBBox, polyBBox)) return false;
		for (const point of tilePoints) if (!pointWithinPolygons(point, tilePolygons)) return false;
	}
	return true;
}
function linesWithinPolygons(ctx, polygonGeometry) {
	const lineBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const polyBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const canonical = ctx.canonicalID();
	if (polygonGeometry.type === "Polygon") {
		const tilePolygon = getTilePolygon(polygonGeometry.coordinates, polyBBox, canonical);
		const tileLines = getTileLines(ctx.geometry(), lineBBox, polyBBox, canonical);
		if (!boxWithinBox(lineBBox, polyBBox)) return false;
		for (const line of tileLines) if (!lineStringWithinPolygon(line, tilePolygon)) return false;
	}
	if (polygonGeometry.type === "MultiPolygon") {
		const tilePolygons = getTilePolygons(polygonGeometry.coordinates, polyBBox, canonical);
		const tileLines = getTileLines(ctx.geometry(), lineBBox, polyBBox, canonical);
		if (!boxWithinBox(lineBBox, polyBBox)) return false;
		for (const line of tileLines) if (!lineStringWithinPolygons(line, tilePolygons)) return false;
	}
	return true;
}
var Within = class Within {
	constructor(geojson, geometries) {
		this.type = BooleanType;
		this.geojson = geojson;
		this.geometries = geometries;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`'within' expression requires exactly one argument, but found ${args.length - 1} instead.`);
		if (isValue(args[1])) {
			const geojson = args[1];
			if (geojson.type === "FeatureCollection") {
				const polygonsCoords = [];
				for (const polygon of geojson.features) {
					const { type, coordinates } = polygon.geometry;
					if (type === "Polygon") polygonsCoords.push(coordinates);
					if (type === "MultiPolygon") polygonsCoords.push(...coordinates);
				}
				if (polygonsCoords.length) return new Within(geojson, {
					type: "MultiPolygon",
					coordinates: polygonsCoords
				});
			} else if (geojson.type === "Feature") {
				const type = geojson.geometry.type;
				if (type === "Polygon" || type === "MultiPolygon") return new Within(geojson, geojson.geometry);
			} else if (geojson.type === "Polygon" || geojson.type === "MultiPolygon") return new Within(geojson, geojson);
		}
		return context.error("'within' expression requires valid geojson object that contains polygon geometry type.");
	}
	evaluate(ctx) {
		if (ctx.geometry() != null && ctx.canonicalID() != null) {
			if (ctx.geometryType() === "Point") return pointsWithinPolygons(ctx, this.geometries);
			else if (ctx.geometryType() === "LineString") return linesWithinPolygons(ctx, this.geometries);
		}
		return false;
	}
	eachChild() {}
	outputDefined() {
		return true;
	}
};
//#endregion
export { Within };

//# sourceMappingURL=within.mjs.map