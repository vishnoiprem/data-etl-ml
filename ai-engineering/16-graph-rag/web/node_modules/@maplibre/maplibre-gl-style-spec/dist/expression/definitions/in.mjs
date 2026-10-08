import { BooleanType, NullType, NumberType, StringType, ValueType, isValidNativeType, isValidType, typeToString } from "../types.mjs";
import { RuntimeError } from "../runtime_error.mjs";
import { typeOf } from "../values.mjs";
//#region src/expression/definitions/in.ts
var In = class In {
	constructor(needle, haystack, key) {
		this.needle = needle;
		this.haystack = haystack;
		this.key = key;
		this.type = BooleanType;
	}
	static parse(args, context) {
		if (args.length !== 3) return context.error(`Expected 2 arguments, but found ${args.length - 1} instead.`);
		const needle = context.parse(args[1], 1, ValueType);
		const haystack = context.parse(args[2], 2, ValueType);
		if (!needle || !haystack) return null;
		if (!isValidType(needle.type, [
			BooleanType,
			StringType,
			NumberType,
			NullType,
			ValueType
		])) return context.error(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(needle.type)} instead`);
		return new In(needle, haystack, context.key);
	}
	evaluate(ctx) {
		const needle = this.needle.evaluate(ctx);
		const haystack = this.haystack.evaluate(ctx);
		if (!haystack) return false;
		if (!isValidNativeType(needle, [
			"boolean",
			"string",
			"number",
			"null"
		])) throw new RuntimeError(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(typeOf(needle))} instead.`, this.key);
		if (!isValidNativeType(haystack, ["string", "array"])) throw new RuntimeError(`Expected second argument to be of type array or string, but found ${typeToString(typeOf(haystack))} instead.`, this.key);
		return haystack.indexOf(needle) >= 0;
	}
	eachChild(fn) {
		fn(this.needle);
		fn(this.haystack);
	}
	outputDefined() {
		return true;
	}
};
//#endregion
export { In };

//# sourceMappingURL=in.mjs.map