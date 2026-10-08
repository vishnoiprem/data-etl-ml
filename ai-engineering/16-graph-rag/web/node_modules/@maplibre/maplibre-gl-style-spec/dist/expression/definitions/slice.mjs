import { NumberType, StringType, ValueType, array, isValidNativeType, isValidType, typeToString } from "../types.mjs";
import { RuntimeError } from "../runtime_error.mjs";
import { typeOf } from "../values.mjs";
//#region src/expression/definitions/slice.ts
var Slice = class Slice {
	constructor(type, input, beginIndex, key, endIndex) {
		this.type = type;
		this.input = input;
		this.beginIndex = beginIndex;
		this.key = key;
		this.endIndex = endIndex;
	}
	static parse(args, context) {
		if (args.length <= 2 || args.length >= 5) return context.error(`Expected 2 or 3 arguments, but found ${args.length - 1} instead.`);
		const input = context.parse(args[1], 1, ValueType);
		const beginIndex = context.parse(args[2], 2, NumberType);
		if (!input || !beginIndex) return null;
		if (!isValidType(input.type, [
			array(ValueType),
			StringType,
			ValueType
		])) return context.error(`Expected first argument to be of type array or string, but found ${typeToString(input.type)} instead`);
		if (args.length === 4) {
			const endIndex = context.parse(args[3], 3, NumberType);
			if (!endIndex) return null;
			return new Slice(input.type, input, beginIndex, context.key, endIndex);
		} else return new Slice(input.type, input, beginIndex, context.key);
	}
	evaluate(ctx) {
		const input = this.input.evaluate(ctx);
		const beginIndex = this.beginIndex.evaluate(ctx);
		let endIndex;
		if (this.endIndex) endIndex = this.endIndex.evaluate(ctx);
		if (isValidNativeType(input, ["string"])) return [...input].slice(beginIndex, endIndex).join("");
		else if (isValidNativeType(input, ["array"])) return input.slice(beginIndex, endIndex);
		else throw new RuntimeError(`Expected first argument to be of type array or string, but found ${typeToString(typeOf(input))} instead.`, this.key);
	}
	eachChild(fn) {
		fn(this.input);
		fn(this.beginIndex);
		if (this.endIndex) fn(this.endIndex);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
export { Slice };

//# sourceMappingURL=slice.mjs.map