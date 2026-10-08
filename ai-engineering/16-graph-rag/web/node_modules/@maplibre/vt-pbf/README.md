[![MapLibre Logo](https://maplibre.org/img/maplibre-logo-big.svg)](https://maplibre.org/)

# vt-pbf 
[![NPM Version](https://img.shields.io/npm/v/@maplibre/vt-pbf.svg)](https://www.npmjs.com/package/@maplibre/vt-pbf)

Serialize [Mapbox vector tiles](https://github.com/mapbox/vector-tile-spec) to binary protobufs in javascript.

## Installation
Using NPM: `npm install @maplibre/vt-pbf`

Or `npm run build` and find build artifacts in `dist/`

## Usage

As far as I know, the two places you might get a JS representation of a vector
tile are [geojson-vt](https://github.com/mapbox/geojson-vt) and
[vector-tile-js](https://github.com/mapbox/vector-tile-js).  These both use
slightly different internal representations, so serializing each looks slightly
different:

## From vector-tile-js

```javascript
import {fromVectorTileJs} from 'vt-pbf'
import {VectorTile} = from '@mapbox/vector-tile'
import Protobuf from 'pbf'

var data = fs.readFileSync(__dirname + '/fixtures/rectangle-1.0.0.pbf')
var tile = new VectorTile(new Protobuf(data))
var orig = tile.layers['geojsonLayer'].feature(0).toGeoJSON(0, 0, 1)

var buff = fromVectorTileJs(tile)
fs.writeFileSync('my-tile.pbf', buff)
```

## From geojson-vt

```javascript
import {fromGeojsonVt} from 'vt-pbf'
import geojsonVt from '@maplibre/geojson-vt'

var orig = JSON.parse(fs.readFileSync(__dirname + '/fixtures/rectangle.geojson'))
var tileindex = geojsonVt(orig)
var tile = tileindex.getTile(1, 0, 0)

// pass in an object mapping layername -> tile object
var buff = fromGeojsonVt({ 'geojsonLayer': tile })
fs.writeFileSync('my-tile.pbf', buff)
```

`fromGeojsonVt` takes two arguments:
- `layerMap` is an object where keys are layer names and values are a geojson-vt tile,
- `options` is an object (optional argument). There are 2 supported keys: `version` to define the version of the mvt spec used and `extent` to define the extent of the tile. `version` defaults to 1 and `extent` to 4096.

