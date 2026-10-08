import { isValue, typeOf } from "../values.mjs";
//#region src/expression/definitions/literal.ts
var Literal = class Literal {
	constructor(type, value) {
		this.type = type;
		this.value = value;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`'literal' expression requires exactly one argument, but found ${args.length - 1} instead.`);
		if (!isValue(args[1])) return context.error(`invalid value of type "${typeof args[1]}"`);
		const value = args[1];
		let type = typeOf(value);
		const expected = context.expectedType;
		if (type.kind === "array" && type.N === 0 && expected && expected.kind === "array" && (typeof expected.N !== "number" || expected.N === 0)) type = expected;
		return new Literal(type, value);
	}
	evaluate() {
		return this.value;
	}
	eachChild() {}
	outputDefined() {
		return true;
	}
};
//#endregion
export { Literal };

//# sourceMappingURL=literal.mjs.map