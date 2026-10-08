//#region src/expression/types.ts
const NullType = { kind: "null" };
const NumberType = { kind: "number" };
const StringType = { kind: "string" };
const BooleanType = { kind: "boolean" };
const ColorType = { kind: "color" };
const ProjectionDefinitionType = { kind: "projectionDefinition" };
const ObjectType = { kind: "object" };
const ValueType = { kind: "value" };
const ErrorType = { kind: "error" };
const CollatorType = { kind: "collator" };
const FormattedType = { kind: "formatted" };
const PaddingType = { kind: "padding" };
const ColorArrayType = { kind: "colorArray" };
const NumberArrayType = { kind: "numberArray" };
const ResolvedImageType = { kind: "resolvedImage" };
const VariableAnchorOffsetCollectionType = { kind: "variableAnchorOffsetCollection" };
function array(itemType, N) {
	return {
		kind: "array",
		itemType,
		N
	};
}
function typeToString(type) {
	if (type.kind === "array") {
		const itemType = typeToString(type.itemType);
		return typeof type.N === "number" ? `array<${itemType}, ${type.N}>` : type.itemType.kind === "value" ? "array" : `array<${itemType}>`;
	} else return type.kind;
}
const valueMemberTypes = [
	NullType,
	NumberType,
	StringType,
	BooleanType,
	ColorType,
	ProjectionDefinitionType,
	FormattedType,
	ObjectType,
	array(ValueType),
	PaddingType,
	NumberArrayType,
	ColorArrayType,
	ResolvedImageType,
	VariableAnchorOffsetCollectionType
];
/**
* Returns null if `t` is a subtype of `expected`; otherwise returns an
* error message.
* @private
*/
function checkSubtype(expected, t) {
	if (t.kind === "error") return null;
	else if (expected.kind === "array") {
		if (t.kind === "array" && (t.N === 0 && t.itemType.kind === "value" || !checkSubtype(expected.itemType, t.itemType)) && (typeof expected.N !== "number" || expected.N === t.N)) return null;
	} else if (expected.kind === t.kind) return null;
	else if (expected.kind === "value") {
		for (const memberType of valueMemberTypes) if (!checkSubtype(memberType, t)) return null;
	}
	return `Expected ${typeToString(expected)} but found ${typeToString(t)} instead.`;
}
function isValidType(provided, allowedTypes) {
	return allowedTypes.some((t) => t.kind === provided.kind);
}
function isValidNativeType(provided, allowedTypes) {
	return allowedTypes.some((t) => {
		if (t === "null") return provided === null;
		else if (t === "array") return Array.isArray(provided);
		else if (t === "object") return provided && !Array.isArray(provided) && typeof provided === "object";
		else return t === typeof provided;
	});
}
/**
* Verify whether the specified type is of the same type as the specified sample.
*
* @param provided Type to verify
* @param sample Sample type to reference
* @returns `true` if both objects are of the same type, `false` otherwise
* @example basic types
* if (verifyType(outputType, ValueType)) {
*     // type narrowed to:
*     outputType.kind; // 'value'
* }
* @example array types
* if (verifyType(outputType, array(NumberType))) {
*     // type narrowed to:
*     outputType.kind; // 'array'
*     outputType.itemType; // NumberTypeT
*     outputType.itemType.kind; // 'number'
* }
*/
function verifyType(provided, sample) {
	if (provided.kind === "array" && sample.kind === "array") return provided.itemType.kind === sample.itemType.kind && typeof provided.N === "number";
	return provided.kind === sample.kind;
}
//#endregion
export { BooleanType, CollatorType, ColorArrayType, ColorType, ErrorType, FormattedType, NullType, NumberArrayType, NumberType, ObjectType, PaddingType, ProjectionDefinitionType, ResolvedImageType, StringType, ValueType, VariableAnchorOffsetCollectionType, array, checkSubtype, isValidNativeType, isValidType, typeToString, verifyType };

//# sourceMappingURL=types.mjs.map