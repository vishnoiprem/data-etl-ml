import { ValueType, array } from "../types.mjs";
import { isValue, typeOf } from "../values.mjs";
import { Literal } from "./literal.mjs";
//#region src/expression/definitions/semiliteral.ts
var Semiliteral = class Semiliteral {
	constructor(arr) {
		let elementType = null;
		for (const expr of arr) if (!elementType) elementType = expr.type;
		else if (elementType === expr.type) continue;
		else {
			elementType = ValueType;
			break;
		}
		this.type = array(elementType ?? ValueType, arr.length);
		this.arr = arr;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`'semiliteral' expression requires exactly one argument, but found ${args.length - 1} instead.`);
		if (!isValue(args[1])) return context.error(`invalid value of type "${typeof args[1]}"`);
		const value = args[1];
		const type = typeOf(value);
		if (type.kind === "array") {
			const arr = value;
			const arrayContext = context.concat(1);
			const parsed = [];
			for (let i = 0; i < arr.length; i++) {
				const item = arrayContext.parse(arr[i], i, ValueType);
				if (!item) return null;
				parsed.push(item);
			}
			return new Semiliteral(parsed);
		} else return new Literal(type, value);
	}
	evaluate(ctx) {
		return this.arr.map((arg) => arg.evaluate(ctx));
	}
	eachChild(fn) {
		this.arr.forEach(fn);
	}
	outputDefined() {
		return this.arr.every((arg) => arg.outputDefined());
	}
};
//#endregion
export { Semiliteral };

//# sourceMappingURL=semiliteral.mjs.map