import { interpolateArray } from "../../util/interpolate-primitives.mjs";
//#region src/expression/types/number_array.ts
/**
* An array of numbers. Create instances from
* bare arrays or numeric values using the static method `NumberArray.parse`.
* @private
*/
var NumberArray = class NumberArray {
	constructor(values) {
		this.values = values.slice();
	}
	/**
	* Numeric NumberArray values
	* @param input A NumberArray value
	* @returns A `NumberArray` instance, or `undefined` if the input is not a valid NumberArray value.
	*/
	static parse(input) {
		if (input instanceof NumberArray) return input;
		if (typeof input === "number") return new NumberArray([input]);
		if (!Array.isArray(input)) return;
		for (const val of input) if (typeof val !== "number") return;
		return new NumberArray(input);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t) {
		return new NumberArray(interpolateArray(from.values, to.values, t));
	}
};
//#endregion
export { NumberArray };

//# sourceMappingURL=number_array.mjs.map