import { NumberType, typeToString } from "../types.mjs";
import { RuntimeError } from "../runtime_error.mjs";
import { typeOf } from "../values.mjs";
//#region src/expression/definitions/length.ts
var Length = class Length {
	constructor(input, key) {
		this.input = input;
		this.key = key;
		this.type = NumberType;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`Expected 1 argument, but found ${args.length - 1} instead.`);
		const input = context.parse(args[1], 1);
		if (!input) return null;
		if (input.type.kind !== "array" && input.type.kind !== "string" && input.type.kind !== "value") return context.error(`Expected argument of type string or array, but found ${typeToString(input.type)} instead.`);
		return new Length(input, context.key);
	}
	evaluate(ctx) {
		const input = this.input.evaluate(ctx);
		if (typeof input === "string") return [...input].length;
		else if (Array.isArray(input)) return input.length;
		else throw new RuntimeError(`Expected value to be of type string or array, but found ${typeToString(typeOf(input))} instead.`, this.key);
	}
	eachChild(fn) {
		fn(this.input);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
export { Length };

//# sourceMappingURL=length.mjs.map