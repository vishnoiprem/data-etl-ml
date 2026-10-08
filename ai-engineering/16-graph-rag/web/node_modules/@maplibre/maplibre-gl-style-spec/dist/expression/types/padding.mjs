import { interpolateArray } from "../../util/interpolate-primitives.mjs";
//#region src/expression/types/padding.ts
/**
* A set of four numbers representing padding around a box. Create instances from
* bare arrays or numeric values using the static method `Padding.parse`.
* @private
*/
var Padding = class Padding {
	constructor(values) {
		this.values = values.slice();
	}
	/**
	* Numeric padding values
	* @param input A padding value
	* @returns A `Padding` instance, or `undefined` if the input is not a valid padding value.
	*/
	static parse(input) {
		if (input instanceof Padding) return input;
		if (typeof input === "number") return new Padding([
			input,
			input,
			input,
			input
		]);
		if (!Array.isArray(input)) return;
		if (input.length < 1 || input.length > 4) return;
		for (const val of input) if (typeof val !== "number") return;
		switch (input.length) {
			case 1:
				input = [
					input[0],
					input[0],
					input[0],
					input[0]
				];
				break;
			case 2:
				input = [
					input[0],
					input[1],
					input[0],
					input[1]
				];
				break;
			case 3: input = [
				input[0],
				input[1],
				input[2],
				input[1]
			];
		}
		return new Padding(input);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t) {
		return new Padding(interpolateArray(from.values, to.values, t));
	}
};
//#endregion
export { Padding };

//# sourceMappingURL=padding.mjs.map