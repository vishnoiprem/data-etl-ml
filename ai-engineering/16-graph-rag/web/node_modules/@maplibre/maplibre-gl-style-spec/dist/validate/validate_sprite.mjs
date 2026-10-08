import { ValidationError } from "../error/validation_error.mjs";
import { validateObject } from "./validate_object.mjs";
import { validateString } from "./validate_string.mjs";
//#region src/validate/validate_sprite.ts
function validateSprite(options) {
	let errors = [];
	const sprite = options.value;
	const key = options.key;
	if (!Array.isArray(sprite)) return validateString({
		key,
		value: sprite
	});
	else {
		const allSpriteIds = [];
		const allSpriteURLs = [];
		for (const i in sprite) {
			if (sprite[i].id && allSpriteIds.includes(sprite[i].id)) errors.push(new ValidationError(key, sprite, `all the sprites' ids must be unique, but ${sprite[i].id} is duplicated`));
			allSpriteIds.push(sprite[i].id);
			if (sprite[i].url && allSpriteURLs.includes(sprite[i].url)) errors.push(new ValidationError(key, sprite, `all the sprites' URLs must be unique, but ${sprite[i].url} is duplicated`));
			allSpriteURLs.push(sprite[i].url);
			errors = errors.concat(validateObject({
				key: `${key}[${i}]`,
				value: sprite[i],
				valueSpec: {
					id: {
						type: "string",
						required: true
					},
					url: {
						type: "string",
						required: true
					}
				},
				validateSpec: options.validateSpec
			}));
		}
		return errors;
	}
}
//#endregion
export { validateSprite };

//# sourceMappingURL=validate_sprite.mjs.map