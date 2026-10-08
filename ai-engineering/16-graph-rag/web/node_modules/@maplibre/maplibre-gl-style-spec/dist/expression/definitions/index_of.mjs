import { BooleanType, NullType, NumberType, StringType, ValueType, isValidNativeType, isValidType, typeToString } from "../types.mjs";
import { RuntimeError } from "../runtime_error.mjs";
import { typeOf } from "../values.mjs";
//#region src/expression/definitions/index_of.ts
var IndexOf = class IndexOf {
	constructor(needle, haystack, key, fromIndex) {
		this.needle = needle;
		this.haystack = haystack;
		this.key = key;
		this.fromIndex = fromIndex;
		this.type = NumberType;
	}
	static parse(args, context) {
		if (args.length <= 2 || args.length >= 5) return context.error(`Expected 2 or 3 arguments, but found ${args.length - 1} instead.`);
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
		if (args.length === 4) {
			const fromIndex = context.parse(args[3], 3, NumberType);
			if (!fromIndex) return null;
			return new IndexOf(needle, haystack, context.key, fromIndex);
		} else return new IndexOf(needle, haystack, context.key);
	}
	evaluate(ctx) {
		const needle = this.needle.evaluate(ctx);
		const haystack = this.haystack.evaluate(ctx);
		if (!isValidNativeType(needle, [
			"boolean",
			"string",
			"number",
			"null"
		])) throw new RuntimeError(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(typeOf(needle))} instead.`, this.key);
		let fromIndex;
		if (this.fromIndex) fromIndex = this.fromIndex.evaluate(ctx);
		if (isValidNativeType(haystack, ["string"])) {
			const rawIndex = haystack.indexOf(needle, fromIndex);
			if (rawIndex === -1) return -1;
			else return [...haystack.slice(0, rawIndex)].length;
		} else if (isValidNativeType(haystack, ["array"])) return haystack.indexOf(needle, fromIndex);
		else throw new RuntimeError(`Expected second argument to be of type array or string, but found ${typeToString(typeOf(haystack))} instead.`, this.key);
	}
	eachChild(fn) {
		fn(this.needle);
		fn(this.haystack);
		if (this.fromIndex) fn(this.fromIndex);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
export { IndexOf };

//# sourceMappingURL=index_of.mjs.map