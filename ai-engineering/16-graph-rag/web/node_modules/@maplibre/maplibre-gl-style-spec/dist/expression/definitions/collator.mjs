import { BooleanType, CollatorType, StringType } from "../types.mjs";
import { Collator } from "../types/collator.mjs";
//#region src/expression/definitions/collator.ts
var CollatorExpression = class CollatorExpression {
	constructor(caseSensitive, diacriticSensitive, locale) {
		this.type = CollatorType;
		this.locale = locale;
		this.caseSensitive = caseSensitive;
		this.diacriticSensitive = diacriticSensitive;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error("Expected one argument.");
		const options = args[1];
		if (typeof options !== "object" || Array.isArray(options)) return context.error("Collator options argument must be an object.");
		const caseSensitive = context.parse(options["case-sensitive"] === void 0 ? false : options["case-sensitive"], 1, BooleanType);
		if (!caseSensitive) return null;
		const diacriticSensitive = context.parse(options["diacritic-sensitive"] === void 0 ? false : options["diacritic-sensitive"], 1, BooleanType);
		if (!diacriticSensitive) return null;
		let locale = null;
		if (options["locale"]) {
			locale = context.parse(options["locale"], 1, StringType);
			if (!locale) return null;
		}
		return new CollatorExpression(caseSensitive, diacriticSensitive, locale);
	}
	evaluate(ctx) {
		return new Collator(this.caseSensitive.evaluate(ctx), this.diacriticSensitive.evaluate(ctx), this.locale ? this.locale.evaluate(ctx) : null);
	}
	eachChild(fn) {
		fn(this.caseSensitive);
		fn(this.diacriticSensitive);
		if (this.locale) fn(this.locale);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
export { CollatorExpression };

//# sourceMappingURL=collator.mjs.map