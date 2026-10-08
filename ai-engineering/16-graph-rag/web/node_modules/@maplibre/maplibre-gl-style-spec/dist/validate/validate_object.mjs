import { ValidationError } from "../error/validation_error.mjs";
import { getOwn } from "../util/get_own.mjs";
import { getType } from "../util/get_type.mjs";
//#region src/validate/validate_object.ts
function validateObject(options) {
	const key = options.key;
	const object = options.value;
	const elementSpecs = options.valueSpec || {};
	const elementValidators = options.objectElementValidators || {};
	const style = options.style;
	const styleSpec = options.styleSpec;
	const validateSpec = options.validateSpec;
	let errors = [];
	const type = getType(object);
	if (type !== "object") return [new ValidationError(key, object, `object expected, ${type} found`)];
	for (const objectKey in object) {
		const elementSpecKey = objectKey.split(".")[0];
		const elementSpec = getOwn(elementSpecs, elementSpecKey) || elementSpecs["*"];
		let validateElement;
		if (getOwn(elementValidators, elementSpecKey)) validateElement = elementValidators[elementSpecKey];
		else if (getOwn(elementSpecs, elementSpecKey)) {
			if (object[objectKey] === void 0) continue;
			validateElement = validateSpec;
		} else if (elementValidators["*"]) validateElement = elementValidators["*"];
		else if (elementSpecs["*"]) validateElement = validateSpec;
		else {
			errors.push(new ValidationError(key, object[objectKey], `unknown property "${objectKey}"`));
			continue;
		}
		errors = errors.concat(validateElement({
			key: (key ? `${key}.` : key) + objectKey,
			value: object[objectKey],
			valueSpec: elementSpec,
			style,
			styleSpec,
			object,
			objectKey,
			validateSpec
		}, object));
	}
	for (const elementSpecKey in elementSpecs) {
		if (elementValidators[elementSpecKey]) continue;
		if (elementSpecs[elementSpecKey].required && elementSpecs[elementSpecKey]["default"] === void 0 && object[elementSpecKey] === void 0) errors.push(new ValidationError(key, object, `missing required property "${elementSpecKey}"`));
	}
	return errors;
}
//#endregion
export { validateObject };

//# sourceMappingURL=validate_object.mjs.map