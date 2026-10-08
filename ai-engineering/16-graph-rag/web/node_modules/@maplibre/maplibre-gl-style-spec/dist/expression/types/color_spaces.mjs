//#region src/expression/types/color_spaces.ts
const Xn = .96422;
const Yn = 1;
const Zn = .82521;
const t0 = 4 / 29;
const t1 = 6 / 29;
const t2 = 3 * t1 * t1;
const t3 = t1 * t1 * t1;
const deg2rad = Math.PI / 180;
const rad2deg = 180 / Math.PI;
function constrainAngle(angle) {
	angle = angle % 360;
	if (angle < 0) angle += 360;
	return angle;
}
function rgbToLab([r, g, b, alpha]) {
	r = rgb2xyz(r);
	g = rgb2xyz(g);
	b = rgb2xyz(b);
	let x, z;
	const y = xyz2lab((.2225045 * r + .7168786 * g + .0606169 * b) / Yn);
	if (r === g && g === b) x = z = y;
	else {
		x = xyz2lab((.4360747 * r + .3850649 * g + .1430804 * b) / Xn);
		z = xyz2lab((.0139322 * r + .0971045 * g + .7141733 * b) / Zn);
	}
	const l = 116 * y - 16;
	return [
		l < 0 ? 0 : l,
		500 * (x - y),
		200 * (y - z),
		alpha
	];
}
function rgb2xyz(x) {
	return x <= .04045 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4);
}
function xyz2lab(t) {
	return t > t3 ? Math.pow(t, 1 / 3) : t / t2 + t0;
}
function labToRgb([l, a, b, alpha]) {
	let y = (l + 16) / 116, x = isNaN(a) ? y : y + a / 500, z = isNaN(b) ? y : y - b / 200;
	y = Yn * lab2xyz(y);
	x = Xn * lab2xyz(x);
	z = Zn * lab2xyz(z);
	return [
		xyz2rgb(3.1338561 * x - 1.6168667 * y - .4906146 * z),
		xyz2rgb(-.9787684 * x + 1.9161415 * y + .033454 * z),
		xyz2rgb(.0719453 * x - .2289914 * y + 1.4052427 * z),
		alpha
	];
}
function xyz2rgb(x) {
	x = x <= .00304 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - .055;
	return x < 0 ? 0 : x > 1 ? 1 : x;
}
function lab2xyz(t) {
	return t > t1 ? t * t * t : t2 * (t - t0);
}
function rgbToHcl(rgbColor) {
	const [l, a, b, alpha] = rgbToLab(rgbColor);
	const c = Math.sqrt(a * a + b * b);
	return [
		Math.round(c * 1e4) ? constrainAngle(Math.atan2(b, a) * rad2deg) : NaN,
		c,
		l,
		alpha
	];
}
function hclToRgb([h, c, l, alpha]) {
	h = isNaN(h) ? 0 : h * deg2rad;
	return labToRgb([
		l,
		Math.cos(h) * c,
		Math.sin(h) * c,
		alpha
	]);
}
function hslToRgb([h, s, l, alpha]) {
	h = constrainAngle(h);
	s /= 100;
	l /= 100;
	function f(n) {
		const k = (n + h / 30) % 12;
		const a = s * Math.min(l, 1 - l);
		return l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
	}
	return [
		f(0),
		f(8),
		f(4),
		alpha
	];
}
//#endregion
export { hclToRgb, hslToRgb, labToRgb, rgbToHcl, rgbToLab };

//# sourceMappingURL=color_spaces.mjs.map