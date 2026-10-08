import { RuntimeError } from "./runtime_error.mjs";
//#region src/expression/stops.ts
/**
* Returns the index of the last stop <= input, or 0 if it doesn't exist.
* @private
*/
function findStopLessThanOrEqualTo(stops, input, key) {
	const lastIndex = stops.length - 1;
	let lowerIndex = 0;
	let upperIndex = lastIndex;
	let currentIndex = 0;
	let currentValue, nextValue;
	while (lowerIndex <= upperIndex) {
		currentIndex = Math.floor((lowerIndex + upperIndex) / 2);
		currentValue = stops[currentIndex];
		nextValue = stops[currentIndex + 1];
		if (currentValue <= input) {
			if (currentIndex === lastIndex || input < nextValue) return currentIndex;
			lowerIndex = currentIndex + 1;
		} else if (currentValue > input) upperIndex = currentIndex - 1;
		else throw new RuntimeError("Input is not a number.", key);
	}
	return 0;
}
//#endregion
export { findStopLessThanOrEqualTo };

//# sourceMappingURL=stops.mjs.map