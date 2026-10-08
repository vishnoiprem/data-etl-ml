//#region src/util/geometry_util.ts
const EXTENT = 8192;
function getTileCoordinates(p, canonical) {
	const x = mercatorXfromLng(p[0]);
	const y = mercatorYfromLat(p[1]);
	const tilesAtZoom = Math.pow(2, canonical.z);
	return [Math.round(x * tilesAtZoom * EXTENT), Math.round(y * tilesAtZoom * EXTENT)];
}
function getLngLatFromTileCoord(coord, canonical) {
	const tilesAtZoom = Math.pow(2, canonical.z);
	const x = (coord[0] / EXTENT + canonical.x) / tilesAtZoom;
	const y = (coord[1] / EXTENT + canonical.y) / tilesAtZoom;
	return [lngFromMercatorXfromLng(x), latFromMercatorY(y)];
}
function mercatorXfromLng(lng) {
	return (180 + lng) / 360;
}
function lngFromMercatorXfromLng(mercatorX) {
	return mercatorX * 360 - 180;
}
function mercatorYfromLat(lat) {
	return (180 - 180 / Math.PI * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360))) / 360;
}
function latFromMercatorY(mercatorY) {
	return 360 / Math.PI * Math.atan(Math.exp((180 - mercatorY * 360) * Math.PI / 180)) - 90;
}
function updateBBox(bbox, coord) {
	bbox[0] = Math.min(bbox[0], coord[0]);
	bbox[1] = Math.min(bbox[1], coord[1]);
	bbox[2] = Math.max(bbox[2], coord[0]);
	bbox[3] = Math.max(bbox[3], coord[1]);
}
function boxWithinBox(bbox1, bbox2) {
	if (bbox1[0] <= bbox2[0]) return false;
	if (bbox1[2] >= bbox2[2]) return false;
	if (bbox1[1] <= bbox2[1]) return false;
	if (bbox1[3] >= bbox2[3]) return false;
	return true;
}
function rayIntersect(p, p1, p2) {
	return p1[1] > p[1] !== p2[1] > p[1] && p[0] < (p2[0] - p1[0]) * (p[1] - p1[1]) / (p2[1] - p1[1]) + p1[0];
}
function pointOnBoundary(p, p1, p2) {
	const x1 = p[0] - p1[0];
	const y1 = p[1] - p1[1];
	const x2 = p[0] - p2[0];
	const y2 = p[1] - p2[1];
	return x1 * y2 - x2 * y1 === 0 && x1 * x2 <= 0 && y1 * y2 <= 0;
}
function segmentIntersectSegment(a, b, c, d) {
	const vectorP = [b[0] - a[0], b[1] - a[1]];
	if (perp([d[0] - c[0], d[1] - c[1]], vectorP) === 0) return false;
	if (twoSided(a, b, c, d) && twoSided(c, d, a, b)) return true;
	return false;
}
function lineIntersectPolygon(p1, p2, polygon) {
	for (const ring of polygon) for (let j = 0; j < ring.length - 1; ++j) if (segmentIntersectSegment(p1, p2, ring[j], ring[j + 1])) return true;
	return false;
}
function pointWithinPolygon(point, rings, trueIfOnBoundary = false) {
	let inside = false;
	for (const ring of rings) for (let j = 0; j < ring.length - 1; j++) {
		if (pointOnBoundary(point, ring[j], ring[j + 1])) return trueIfOnBoundary;
		if (rayIntersect(point, ring[j], ring[j + 1])) inside = !inside;
	}
	return inside;
}
function pointWithinPolygons(point, polygons) {
	for (const polygon of polygons) if (pointWithinPolygon(point, polygon)) return true;
	return false;
}
function lineStringWithinPolygon(line, polygon) {
	for (const point of line) if (!pointWithinPolygon(point, polygon)) return false;
	for (let i = 0; i < line.length - 1; ++i) if (lineIntersectPolygon(line[i], line[i + 1], polygon)) return false;
	return true;
}
function lineStringWithinPolygons(line, polygons) {
	for (const polygon of polygons) if (lineStringWithinPolygon(line, polygon)) return true;
	return false;
}
function perp(v1, v2) {
	return v1[0] * v2[1] - v1[1] * v2[0];
}
function twoSided(p1, p2, q1, q2) {
	const x1 = p1[0] - q1[0];
	const y1 = p1[1] - q1[1];
	const x2 = p2[0] - q1[0];
	const y2 = p2[1] - q1[1];
	const x3 = q2[0] - q1[0];
	const y3 = q2[1] - q1[1];
	const det1 = x1 * y3 - x3 * y1;
	const det2 = x2 * y3 - x3 * y2;
	if (det1 > 0 && det2 < 0 || det1 < 0 && det2 > 0) return true;
	return false;
}
//#endregion
export { EXTENT, boxWithinBox, getLngLatFromTileCoord, getTileCoordinates, lineIntersectPolygon, lineStringWithinPolygon, lineStringWithinPolygons, pointWithinPolygon, pointWithinPolygons, rayIntersect, segmentIntersectSegment, updateBBox };

//# sourceMappingURL=geometry_util.mjs.map