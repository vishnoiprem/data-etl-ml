import { eachProperty } from "./visit.mjs";
import { migrateV8 } from "./migrate/v8.mjs";
import { expressions } from "./migrate/expressions.mjs";
import { migrateColors } from "./migrate/migrate_colors.mjs";
//#region src/migrate.ts
/**
* Migrate a Mapbox/MapLibre GL Style to the latest version.
*
* @param style - a MapLibre Style
* @returns a migrated style
* @example
* const fs = require('fs');
* const migrate = require('@maplibre/maplibre-gl-style-spec').migrate;
* const style = fs.readFileSync('./style.json', 'utf8');
* fs.writeFileSync('./style.json', JSON.stringify(migrate(style)));
*/
function migrate(style) {
	let migrated = false;
	if (style.version === 7) {
		style = migrateV8(style);
		migrated = true;
	}
	if (style.version === 8) {
		migrated = !!expressions(style);
		migrated = true;
	}
	eachProperty(style, {
		paint: true,
		layout: true
	}, ({ value, reference, set }) => {
		if (reference?.type === "color") set(migrateColors(value));
	});
	if (!migrated) throw new Error(`Cannot migrate from ${style.version}`);
	return style;
}
//#endregion
export { migrate };

//# sourceMappingURL=migrate.mjs.map