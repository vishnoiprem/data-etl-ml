import { NumberType, StringType } from "../types.mjs";
//#region src/expression/definitions/number_format.ts
var NumberFormat = class NumberFormat {
	constructor(number, locale, currency, unit, minFractionDigits, maxFractionDigits) {
		this.type = StringType;
		this.number = number;
		this.locale = locale;
		this.currency = currency;
		this.unit = unit;
		this.minFractionDigits = minFractionDigits;
		this.maxFractionDigits = maxFractionDigits;
	}
	static parse(args, context) {
		if (args.length !== 3) return context.error("Expected two arguments.");
		const number = context.parse(args[1], 1, NumberType);
		if (!number) return null;
		const options = args[2];
		if (typeof options !== "object" || Array.isArray(options)) return context.error("NumberFormat options argument must be an object.");
		let locale = null;
		if (options["locale"]) {
			locale = context.parse(options["locale"], 1, StringType);
			if (!locale) return null;
		}
		let currency = null;
		if (options["currency"]) {
			currency = context.parse(options["currency"], 1, StringType);
			if (!currency) return null;
		}
		let unit = null;
		if (options["unit"]) {
			unit = context.parse(options["unit"], 1, StringType);
			if (!unit) return null;
		}
		if (currency && unit) return context.error("NumberFormat options `currency` and `unit` are mutually exclusive");
		let minFractionDigits = null;
		if (options["min-fraction-digits"]) {
			minFractionDigits = context.parse(options["min-fraction-digits"], 1, NumberType);
			if (!minFractionDigits) return null;
		}
		let maxFractionDigits = null;
		if (options["max-fraction-digits"]) {
			maxFractionDigits = context.parse(options["max-fraction-digits"], 1, NumberType);
			if (!maxFractionDigits) return null;
		}
		return new NumberFormat(number, locale, currency, unit, minFractionDigits, maxFractionDigits);
	}
	evaluate(ctx) {
		return new Intl.NumberFormat(this.locale ? this.locale.evaluate(ctx) : [], {
			style: this.currency ? "currency" : this.unit ? "unit" : "decimal",
			currency: this.currency ? this.currency.evaluate(ctx) : void 0,
			unit: this.unit ? this.unit.evaluate(ctx) : void 0,
			minimumFractionDigits: this.minFractionDigits ? this.minFractionDigits.evaluate(ctx) : void 0,
			maximumFractionDigits: this.maxFractionDigits ? this.maxFractionDigits.evaluate(ctx) : void 0
		}).format(this.number.evaluate(ctx));
	}
	eachChild(fn) {
		fn(this.number);
		if (this.locale) fn(this.locale);
		if (this.currency) fn(this.currency);
		if (this.unit) fn(this.unit);
		if (this.minFractionDigits) fn(this.minFractionDigits);
		if (this.maxFractionDigits) fn(this.maxFractionDigits);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
export { NumberFormat };

//# sourceMappingURL=number_format.mjs.map