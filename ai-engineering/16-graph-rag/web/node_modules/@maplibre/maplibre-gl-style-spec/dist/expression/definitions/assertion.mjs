import { BooleanType, NumberType, ObjectType, StringType, ValueType, array, checkSubtype, typeToString } from "../types.mjs";
import { RuntimeError } from "../runtime_error.mjs";
import { typeOf } from "../values.mjs";
//#region src/expression/definitions/assertion.ts
const types = {
	string: StringType,
	number: NumberType,
	boolean: BooleanType,
	object: ObjectType
};
var Assertion = class Assertion {
	constructor(type, args, key) {
		this.type = type;
		this.args = args;
		this.key = key;
	}
	static parse(args, context) {
		if (args.length < 2) return context.error("Expected at least one argument.");
		let i = 1;
		let type;
		const name = args[0];
		if (name === "array") {
			let itemType;
			if (args.length > 2) {
				const type = args[1];
				if (typeof type !== "string" || !(type in types) || type === "object") return context.error("The item type argument of \"array\" must be one of string, number, boolean", 1);
				itemType = types[type];
				i++;
			} else itemType = ValueType;
			let N;
			if (args.length > 3) {
				if (args[2] !== null && (typeof args[2] !== "number" || args[2] < 0 || args[2] !== Math.floor(args[2]))) return context.error("The length argument to \"array\" must be a positive integer literal", 2);
				N = args[2];
				i++;
			}
			type = array(itemType, N);
		} else {
			if (!types[name]) throw new Error(`Types doesn't contain name = ${name}`);
			type = types[name];
		}
		const parsed = [];
		for (; i < args.length; i++) {
			const input = context.parse(args[i], i, ValueType);
			if (!input) return null;
			parsed.push(input);
		}
		return new Assertion(type, parsed, context.key);
	}
	evaluate(ctx) {
		for (let i = 0; i < this.args.length; i++) {
			const value = this.args[i].evaluate(ctx);
			if (!checkSubtype(this.type, typeOf(value))) return value;
			else if (i === this.args.length - 1) throw new RuntimeError(`Expected value to be of type ${typeToString(this.type)}, but found ${typeToString(typeOf(value))} instead.`, this.key);
		}
		throw new Error();
	}
	eachChild(fn) {
		this.args.forEach(fn);
	}
	outputDefined() {
		return this.args.every((arg) => arg.outputDefined());
	}
};
//#endregion
export { Assertion };

//# sourceMappingURL=assertion.mjs.map