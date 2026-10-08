import { interpolateNumber } from "../../util/interpolate-primitives.mjs";
import { RuntimeError } from "../runtime_error.mjs";
//#region src/expression/types/variable_anchor_offset_collection.ts
/** Set of valid anchor positions, as a set for validation */
const anchors = /* @__PURE__ */ new Set([
	"center",
	"left",
	"right",
	"top",
	"bottom",
	"top-left",
	"top-right",
	"bottom-left",
	"bottom-right"
]);
/**
* Utility class to assist managing values for text-variable-anchor-offset property. Create instances from
* bare arrays using the static method `VariableAnchorOffsetCollection.parse`.
* @private
*/
var VariableAnchorOffsetCollection = class VariableAnchorOffsetCollection {
	constructor(values) {
		this.values = values.slice();
	}
	static parse(input) {
		if (input instanceof VariableAnchorOffsetCollection) return input;
		if (!Array.isArray(input) || input.length < 1 || input.length % 2 !== 0) return;
		for (let i = 0; i < input.length; i += 2) {
			const anchorValue = input[i];
			const offsetValue = input[i + 1];
			if (typeof anchorValue !== "string" || !anchors.has(anchorValue)) return;
			if (!Array.isArray(offsetValue) || offsetValue.length !== 2 || typeof offsetValue[0] !== "number" || typeof offsetValue[1] !== "number") return;
		}
		return new VariableAnchorOffsetCollection(input);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t, key) {
		const fromValues = from.values;
		const toValues = to.values;
		if (fromValues.length !== toValues.length) throw new RuntimeError(`Cannot interpolate values of different length. from: ${from.toString()}, to: ${to.toString()}`, key);
		const output = [];
		for (let i = 0; i < fromValues.length; i += 2) {
			if (fromValues[i] !== toValues[i]) throw new RuntimeError(`Cannot interpolate values containing mismatched anchors. from[${i}]: ${fromValues[i]}, to[${i}]: ${toValues[i]}`, key);
			output.push(fromValues[i]);
			const [fx, fy] = fromValues[i + 1];
			const [tx, ty] = toValues[i + 1];
			output.push([interpolateNumber(fx, tx, t), interpolateNumber(fy, ty, t)]);
		}
		return new VariableAnchorOffsetCollection(output);
	}
};
//#endregion
export { VariableAnchorOffsetCollection };

//# sourceMappingURL=variable_anchor_offset_collection.mjs.map