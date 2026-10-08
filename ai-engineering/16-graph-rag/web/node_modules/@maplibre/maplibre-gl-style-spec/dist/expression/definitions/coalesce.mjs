import { ValueType, checkSubtype } from "../types.mjs";
import { ResolvedImage } from "../types/resolved_image.mjs";
//#region src/expression/definitions/coalesce.ts
var Coalesce = class Coalesce {
	constructor(type, args) {
		this.type = type;
		this.args = args;
	}
	static parse(args, context) {
		if (args.length < 2) return context.error("Expected at least one argument.");
		let outputType = null;
		const expectedType = context.expectedType;
		if (expectedType && expectedType.kind !== "value") outputType = expectedType;
		const parsedArgs = [];
		for (const arg of args.slice(1)) {
			const parsed = context.parse(arg, 1 + parsedArgs.length, outputType, void 0, { typeAnnotation: "omit" });
			if (!parsed) return null;
			outputType = outputType || parsed.type;
			parsedArgs.push(parsed);
		}
		if (!outputType) throw new Error("No output type");
		return expectedType && parsedArgs.some((arg) => checkSubtype(expectedType, arg.type)) ? new Coalesce(ValueType, parsedArgs) : new Coalesce(outputType, parsedArgs);
	}
	evaluate(ctx) {
		let result = null;
		let argCount = 0;
		let requestedImageName;
		for (const arg of this.args) {
			argCount++;
			result = arg.evaluate(ctx);
			if (result && result instanceof ResolvedImage && !result.available) {
				if (!requestedImageName) requestedImageName = result.name;
				result = null;
				if (argCount === this.args.length) result = requestedImageName;
			}
			if (result !== null) break;
		}
		return result;
	}
	eachChild(fn) {
		this.args.forEach(fn);
	}
	outputDefined() {
		return this.args.every((arg) => arg.outputDefined());
	}
};
//#endregion
export { Coalesce };

//# sourceMappingURL=coalesce.mjs.map