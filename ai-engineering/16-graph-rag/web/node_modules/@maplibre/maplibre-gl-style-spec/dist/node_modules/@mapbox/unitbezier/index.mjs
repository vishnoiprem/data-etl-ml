//#region node_modules/@mapbox/unitbezier/index.js
function unitBezier(p1x, p1y, p2x, p2y) {
	const cx = 3 * p1x;
	const bx = 3 * (p2x - p1x) - cx;
	const ax = 1 - cx - bx;
	const cy = 3 * p1y;
	const by = 3 * (p2y - p1y) - cy;
	const ay = 1 - cy - by;
	return function solve(x, epsilon = 1e-6) {
		if (x <= 0) return 0;
		if (x >= 1) return 1;
		let t = x;
		for (let i = 0; i < 8; i++) {
			const x2 = ((ax * t + bx) * t + cx) * t - x;
			if (Math.abs(x2) < epsilon) return ((ay * t + by) * t + cy) * t;
			const d2 = (3 * ax * t + 2 * bx) * t + cx;
			if (Math.abs(d2) < 1e-6) break;
			t -= x2 / d2;
		}
		let t0 = 0;
		let t1 = 1;
		t = x;
		for (let i = 0; i < 20; i++) {
			const x2 = ((ax * t + bx) * t + cx) * t;
			if (Math.abs(x2 - x) < epsilon) break;
			if (x > x2) t0 = t;
			else t1 = t;
			t = (t0 + t1) * .5;
		}
		return ((ay * t + by) * t + cy) * t;
	};
}
//#endregion
export { unitBezier as default };

//# sourceMappingURL=index.mjs.map