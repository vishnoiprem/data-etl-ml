import quickselect from "../node_modules/quickselect/index.mjs";
//#region src/util/classify_rings.ts
/**
* Classifies an array of rings into polygons with outer rings and holes
* @param rings - the rings to classify
* @param maxRings - the maximum number of rings to include in a polygon, use 0 to include all rings
* @returns an array of polygons with internal rings as holes
*/
function classifyRings(rings, maxRings) {
	if (rings.length <= 1) return [rings];
	const polygons = [];
	let polygon;
	let ccw;
	for (const ring of rings) {
		const area = calculateSignedArea(ring);
		if (area === 0) continue;
		ring.area = Math.abs(area);
		if (ccw === void 0) ccw = area < 0;
		if (ccw === area < 0) {
			if (polygon) polygons.push(polygon);
			polygon = [ring];
		} else polygon.push(ring);
	}
	if (polygon) polygons.push(polygon);
	if (maxRings > 1) for (let j = 0; j < polygons.length; j++) {
		if (polygons[j].length <= maxRings) continue;
		quickselect(polygons[j], maxRings, 1, polygons[j].length - 1, compareAreas);
		polygons[j] = polygons[j].slice(0, maxRings);
	}
	return polygons;
}
function compareAreas(a, b) {
	return b.area - a.area;
}
/**
* Returns the signed area for the polygon ring.  Positive areas are exterior rings and
* have a clockwise winding.  Negative areas are interior rings and have a counter clockwise
* ordering.
*
* @param ring - Exterior or interior ring
* @returns Signed area
*/
function calculateSignedArea(ring) {
	let sum = 0;
	for (let i = 0, len = ring.length, j = len - 1, p1, p2; i < len; j = i++) {
		p1 = ring[i];
		p2 = ring[j];
		sum += (p2.x - p1.x) * (p1.y + p2.y);
	}
	return sum;
}
//#endregion
export { classifyRings };

//# sourceMappingURL=classify_rings.mjs.map