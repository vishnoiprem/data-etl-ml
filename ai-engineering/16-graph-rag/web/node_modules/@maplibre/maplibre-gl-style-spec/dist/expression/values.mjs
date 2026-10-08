import { BooleanType, CollatorType, ColorArrayType, ColorType, FormattedType, NullType, NumberArrayType, NumberType, ObjectType, PaddingType, ProjectionDefinitionType, ResolvedImageType, StringType, ValueType, VariableAnchorOffsetCollectionType, array } from "./types.mjs";
import { Color } from "./types/color.mjs";
import { Collator } from "./types/collator.mjs";
import { Formatted } from "./types/formatted.mjs";
import { Padding } from "./types/padding.mjs";
import { NumberArray } from "./types/number_array.mjs";
import { ColorArray } from "./types/color_array.mjs";
import { VariableAnchorOffsetCollection } from "./types/variable_anchor_offset_collection.mjs";
import { ResolvedImage } from "./types/resolved_image.mjs";
import { ProjectionDefinition } from "./types/projection_definition.mjs";
//#region src/expression/values.ts
function validateRGBA(r, g, b, a) {
	if (!(typeof r === "number" && r >= 0 && r <= 255 && typeof g === "number" && g >= 0 && g <= 255 && typeof b === "number" && b >= 0 && b <= 255)) return `Invalid rgba value [${(typeof a === "number" ? [
		r,
		g,
		b,
		a
	] : [
		r,
		g,
		b
	]).join(", ")}]: 'r', 'g', and 'b' must be between 0 and 255.`;
	if (!(typeof a === "undefined" || typeof a === "number" && a >= 0 && a <= 1)) return `Invalid rgba value [${[
		r,
		g,
		b,
		a
	].join(", ")}]: 'a' must be between 0 and 1.`;
	return null;
}
function isValue(mixed) {
	if (mixed === null || typeof mixed === "string" || typeof mixed === "boolean" || typeof mixed === "number" || mixed instanceof ProjectionDefinition || mixed instanceof Color || mixed instanceof Collator || mixed instanceof Formatted || mixed instanceof Padding || mixed instanceof NumberArray || mixed instanceof ColorArray || mixed instanceof VariableAnchorOffsetCollection || mixed instanceof ResolvedImage) return true;
	else if (Array.isArray(mixed)) {
		for (const item of mixed) if (!isValue(item)) return false;
		return true;
	} else if (typeof mixed === "object") {
		for (const key in mixed) if (!isValue(mixed[key])) return false;
		return true;
	} else return false;
}
function typeOf(value) {
	if (value === null) return NullType;
	else if (typeof value === "string") return StringType;
	else if (typeof value === "boolean") return BooleanType;
	else if (typeof value === "number") return NumberType;
	else if (value instanceof Color) return ColorType;
	else if (value instanceof ProjectionDefinition) return ProjectionDefinitionType;
	else if (value instanceof Collator) return CollatorType;
	else if (value instanceof Formatted) return FormattedType;
	else if (value instanceof Padding) return PaddingType;
	else if (value instanceof NumberArray) return NumberArrayType;
	else if (value instanceof ColorArray) return ColorArrayType;
	else if (value instanceof VariableAnchorOffsetCollection) return VariableAnchorOffsetCollectionType;
	else if (value instanceof ResolvedImage) return ResolvedImageType;
	else if (Array.isArray(value)) {
		const length = value.length;
		let itemType;
		for (const item of value) {
			const t = typeOf(item);
			if (!itemType) itemType = t;
			else if (itemType === t) continue;
			else {
				itemType = ValueType;
				break;
			}
		}
		return array(itemType || ValueType, length);
	} else return ObjectType;
}
function valueToString(value) {
	const type = typeof value;
	if (value === null) return "";
	else if (type === "string" || type === "number" || type === "boolean") return String(value);
	else if (value instanceof Color || value instanceof ProjectionDefinition || value instanceof Formatted || value instanceof Padding || value instanceof NumberArray || value instanceof ColorArray || value instanceof VariableAnchorOffsetCollection || value instanceof ResolvedImage) return value.toString();
	else return JSON.stringify(value);
}
//#endregion
export { isValue, typeOf, validateRGBA, valueToString };

//# sourceMappingURL=values.mjs.map